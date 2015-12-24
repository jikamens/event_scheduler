"""Python Event Scheduler

Match event attendees with topics and time slots based on preferences.

Example::

  from event_scheduler import Scheduler

  s = Scheduler()

  # Time slots have arbitrary names.
  s.add_time_slot('9:30')
  s.add_time_slot('10:30')
  s.add_time_slot('11:30')
  etc.
  ... or ...
  s.add_time_slots('9:30', '10:30', '11:30')

  s.add_topic('Underwater basket-weaving',
              # Time slots and capacities
              (('9:30', 10), ('10:30', 10)))
  s.add_topic('Psychology of auto repair',
              (('10:30', 25), ('11:30', 25)))
  etc.

  s.add_attendee('John Doe', 'Acme, Inc.',
                 # Topic choices from most to least preferred
                 ('Underwater basket-weaving',
                  'History of yarn cultivation',
                  'Wasting time for fun and profit'))
  s.add_attendee('Jane Doe', 'Widgets LLC',
                 # Topic choices from most to least preferred
                 ('Managing the dual-career family',))
  etc.

  # It's a popular topic, but he asked nicely, so make sure he gets it.
  s.manually_assign('John Doe', 'History of yarn cultivation')

  # Where the magic happens
  s.schedule()

See the documentation for individual classes for more
information. You'll mostly care about the ``Scheduler`` class.

TODO
----

Pull requests welcome!

PyPI

Sphinx-ify documentation?

Manual assignment should include assignment to specific sessions.

It should be possible to specific specific time slots for attendees.

Overlapping time slots? Probably significantly more complicated.

There are circumstances when scheduling fails when it probably could
succeed with more aggressive efforts.

Different session-filling algorithms (e.g., fill sessions in order
rather than filling them evenly).

More formatting options for scheduling results.

Optionally ordering attendees by random shuffling rather than by name,
so that multiple runs of the scheduler yield different
assignments. This might also help to address "There are circumstances
when scheduling fails...", since it would enable the user to try to
schedule repeatedly until scheduling succeeds.

Support multiple sessions for a topic in a single time-slot.

Tests.

CREDITS
-------

Written and maintained by Jonathan Kamens <jik@kamens.us>.

CONTACT
-------

Hosted at https://github.com/jikamens/event_scheduler. Feel free to
submit issues or pull requests there!

You can also email me at jik@kamens.us with any questions.

COPYRIGHT
---------

Copyright (c) 2015 Jonathan Kamens.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from collections import defaultdict
from functools import partial
import random


class Scheduler(object):
    """Main scheduling class

    Public properties
    -----------------

    ``time_slots``
        Dictionary of name => ``TimeSlot`` objects, added with
        ``add_time_slot`` or ``add_time_slots``
    ``topics``
        Dictionary of name => ``Topic`` objects, added with
        ``add_topic``
    ``attendees``
        Dictionary of ``"{org} - {name}"`` => ``Attendee`` objects,
        added with ``add_attendee``

    Checkpointing
    -------------

    Checkpointing makes it easier to experiment with different
    scheduling options. You can checkpoint the current state of
    assignments at any time, rollback to the last checkpoint you
    created, or commit the last checkpoint you created. Once you
    rollback or commit a checkpoint, you can then rollback or commit
    the one before that, etc. To prevent programming errors, the
    checkpoint's name must be specified when committing or rolling
    back.
    """

    def __init__(self):
        self.attendees = {}
        self.time_slots = {}
        self.topics = {}
        self.history = []

    def add_time_slots(self, names):
        """Add multiple time slots at once."""

        map(self.add_time_slot, names)

    def add_time_slot(self, name):
        """Add a time slot.

        Time slot names must be unique.
        """

        time_slot = TimeSlot(name)
        if unicode(time_slot) in self.time_slots:
            raise Exception('Attempt to add duplicate time-slot {}'.format(
                time_slot))
        self.time_slots[unicode(time_slot)] = time_slot

    def add_topic(self, name, time_slots):
        """Add a topic.

        ``time_slots`` contains tuples of slot, capacity.
        """

        time_slots = [(t[0] if isinstance(t[0], TimeSlot)
                       else self.time_slots[unicode(t[0])], t[1])
                      for t in time_slots]
        topic = Topic(name, time_slots)
        if unicode(topic) in self.topics:
            raise Exception(u'Attempt to add duplicate topic {}'.format(
                topic))
        self.topics[unicode(topic)] = topic

    def add_attendee(self, name, organization, topics):
        """Add an attendee.

        The combination of name and organization for attendees must be
        unique.

        ``topics`` is a list of topics in preference order. Topics can
        be specified as names or ``Topic`` objects.
        """

        topics = [t if isinstance(t, Topic) else self.topics[t]
                  for t in topics]
        attendee = Attendee(name, organization, topics)
        if unicode(attendee) in self.attendees:
            raise Exception('Attempt to add duplicate attendee {}'.format(
                attendee))
        self.attendees[unicode(attendee)] = attendee

    def manually_assign(self, attendee, topic):
        """Manually assign an attendee to a session for a specific topic.

        The specified topic must appear in the attendee's preferences.

        Sessions assigned manually in this way are immutable, i.e.,
        the scheduling algorithm won't unassign or modify them.

        This is a convenience function that is equivalent to
        ``assign(attendee, topic=topic, immutable=True)``.
        """

        return self.assign(attendee, topic, immutable=True)

    def assign(self, attendee, topic=None, immutable=False):
        """Assign an attendee to their next best available topic session.

        Generally speaking, you will call ``schedule()`` rather than
        calling this method directly. One situation in which you might
        want to call this directly is if there a VIP attendee whom you
        want to schedule first to ensure they get their preferred
        topics.

        You can optionally specify a specific ``topic`` to which to
        assign the attendee.

        You can optionally specify that the assignment is
        ``immutable``, i.e., it should not be unassigned or modified
        once it is made.

        The logic for finding a session to which to assign the
        attendee is simple: the attendee is assigned a session for
        their highest-preference topic for which they haven't already
        been assigned a session and for which a session is available
        in a time-slot they have open.

        Returns True if a session was successfully assigned, or False
        otherwise.
        """

        if not isinstance(attendee, Attendee):
            attendee = next(self.attendees[a] for a in self.attendees
                            if attendee == a)
        if topic is not None and not isinstance(topic, Topic):
            topic = next(self.topics[t] for t in self.topics
                         if topic == t)

        for preference in attendee.preferences:
            if preference.assigned:
                continue
            if topic is not None and topic != preference.topic:
                continue
            ptopic = preference.topic
            for session in sorted(self.topics[unicode(ptopic)].sessions,
                                  key=lambda s: len(s.attendees)):
                try:
                    self._assign(attendee, session, immutable=immutable)
                    return True
                except (SlotConflictError, NoMoreSpaceError):
                    pass
        return False

    def unassign(self, attendee, session, force=False):
        """Unassigned an attendee from a session.

        Won't modify an immutable assignment without ``force=True``.
        """

        try:
            preference = next(p for p in attendee.preferences
                              if p.assignment is not None and
                              p.assignment.session == session)
        except:
            raise Exception(u'{} is not booked for {}'.format(
                attendee, session))
        if preference.assignment.immutable and not force:
            raise Exception(u'{} is required to attend {}'.format(
                attendee, session))

        immutable = preference.assignment.immutable
        preference.assignment = None

        session.attendees = [a for a in session.attendees
                             if a != attendee]

        if self.history:
            self.history[-1].append(
                partial(self._assign, attendee, session, immutable))

    def schedule(self):
        """Automatically schedule attendees in sessions.

        A best effort is made to schedule attendees to attend the
        topics they prefer.

        The scheduling algorithm as it is currently implemented is as
        follows:

        The first phase of scheduling is the time-slot phase, in which
        a pass is made through the attendees for each time-slot (e.g.,
        if there are three time-slots, then there will be three
        passes), and on each pass, an attempt is made to assign a
        session to each attendee whose schedule isn't already
        full. The time-slot phase works as follows:

        * Let n = number of passes in this phase
        * Let m = current pass of this phase, numbered from 0
        * Sort attendees by the sum of their top (n - m) unassigned
          preferences, then in reverse order by the sum of their
          position in prior passes, then by ``"{org} - {name}"`` for
          stability.
        * Skip attendees whose schedules are already full.
        * Try to assign a session to each attendee (see the
          documentation for the ``assign`` method).

        Next is the fill phase, in which we attempt to fill attendee
        schedules that aren't currently filled because the order in
        which sessions were assigned prevented us from assigning
        sessions for some attendees in some passes. See the
        documentation for the ``swap`` method for details on how this
        is done.

        Finally is the improve phase, where we attempt to move around
        assignments to improve the overall happiness of
        attendees. Again, see ``swap`` for additional details.

        Note that this algorithm and implementation don't try to
        create a "perfect" or "optimal" schedule. That's actually a
        pretty hard problem and I'm frankly not sure it's worth the
        effort. The goal is to make reasonably good assignments.
        """

        attendees = self.attendees.values()
        run_order_rankings = defaultdict(int)
        n = len(self.time_slots)
        for m in range(n):
            remaining = n - m
            unassigned_rankings = {
                a: sum([i for i in range(0, len(a.preferences))
                        if not a.preferences[i].assigned][0:remaining])
                for a in attendees
            }
            attendees.sort(key=lambda a: (unassigned_rankings[a],
                                          run_order_rankings[a],
                                          str(a)))
            for i in range(len(attendees)):
                attendee = attendees[i]
                run_order_rankings[attendee] -= i
                if attendee.num_assignments == n:
                    # This person is already full, presumably because of
                    # hard-coded assignments.
                    continue
                if attendee.num_assignments == len(attendee.preferences):
                    # Attendee selected fewer topics than available time
                    # slots, and has already gotten all of them.
                    continue
                self.assign(attendee)
        while any(a for a in attendees
                  if a.num_assignments < min(n, len(a.preferences))):
            attendees.sort(key=lambda a: (a.num_assignments, str(a)))
            changed = False
            for attendee in attendees:
                if attendee.num_assignments == \
                   min(n, len(attendee.preferences)):
                    break
                if self.swap(attendee):
                    changed = True
            if not changed:
                raise ScheduleFailureError(
                    'Could not assign all attendees in fill phase')
        max_preferences = max(len(a.preferences) for a in attendees)
        for cutoff in range(max_preferences, n - 1, -1):
            attendees.sort(key=lambda a: (-a.max_assigned_preference, str(a)))
            if not any(a for a in attendees
                       if a.max_assigned_preference == cutoff):
                continue
            changed = False
            for attendee in attendees:
                if attendee.max_assigned_preference < cutoff:
                    continue
                if self.swap(attendee):
                    changed = True
            if not changed:
                break

    def clear_schedule(self, force=False):
        """Clear all scheduling assignments.

        If ``force=True``, then also clear immutable assignments.
        """

        for attendee in self.attendees:
            for preference in attendee.preferences:
                if preference.assignment is None:
                    continue
                if not force and preference.assignment.immutable:
                    continue
                self.unassign(attendee, preference.assignment.session,
                              force=force)

    def dump(self):
        """Return a string representation of the state of the scheduler."""

        o = 'Attendees:\n\n'
        o += '\n'.join(k.dump() for k in self.attendees.values())

        o += '\nTopics:\n\n'
        o += '\n'.join(t.dump() for t in self.topics.values())
        return o

    def checkpoint(self, name=None):
        """Checkpoint the scheduler state.

        If no name is specified, then a random name will be generated.

        The name of the new checkpoint is returned.
        """

        if name is None:
            name = str(random.random())
        self.history.append([name])
        return name

    def commit(self, name):
        """Commit the most recently created checkpoint.

        The checkpoint itself is removed after the changes are
        committed.

        To prevent programming errors, the name of the checkpoint
        being committed must be specified.

        Once a checkpoint is committed, it can't be rolled
        back. However, if there is an earlier checkpoint that has not
        yet been committed, the newly committed changes become part of
        *that* checkpoint and will be committed or rolled back with
        it.
        """

        assert name == self.history[-1][0]
        if len(self.history) > 1:
            self.history[-2].extend(self.history[-1][1:])
            self.history.pop()
        else:
            self.history = []

    def rollback(self, name):
        """Roll back the most recently created checkpoint.

        All changes since the checkpoint was created are undone, and
        the checkpoint is removed.

        To prevent programming errors, the name of the checkpoint
        being rolled back must be specified.
        """

        assert name == self.history[-1][0]
        for event in reversed(self.history[-1][1:]):
            event()
        self.history.pop()

    def _assign(self, attendee, session, immutable=False):
        if any(p.assignment for p in attendee.preferences
               if p.assignment is not None and
               p.assignment.session.time_slot == session.time_slot):
            raise SlotConflictError('{} is already booked for time-slot {}'.
                                    format(attendee, session.time_slot))

        # We should never be able to exceed capacity, so make this an
        # assertion.
        assert len(session.attendees) <= session.capacity
        if len(session.attendees) == session.capacity:
            raise NoMoreSpaceError(u'No more room for {} in {}'.format(
                attendee, session))

        try:
            preference = next(p for p in attendee.preferences
                              if p.topic == session.topic)
        except:
            raise Exception(u'{} has not asked for topic {}'.format(
                attendee, session.topic))
        if preference.assigned:
            raise Exception(u'{} is already attending topic {}'.format(
                attendee, session.topic))

        preference.assignment = Assignment(session, immutable)

        session.attendees.append(attendee)

        if self.history:
            self.history[-1].append(
                partial(self.unassign, attendee, session, force=True))

    def swap(self, attendee):
        """Try to improve the schedule for an attendee.

        The specified attendee (the "unlucky" attendee) needs
        improvement either because he doesn't have all of his
        assignments, or because he didn't get his top preferences and
        we want to see if we can move people around to make things
        more fair.

        In the former case, we're willing to steal any assignment from
        any other attendee that enables us to fill both attendees'
        sessions.

        In the latter case, we calculate the score of the unlucky
        attendee -- defined as the sum of the preferences he was
        successfully assigned, which obviously means that a lower
        score is better from the point of view of the attendee -- then
        we unassign the worst-assigned preference from the unlucky
        attendee and try to find another attendee we can steal an
        assignment from such that the new score of the unlucky
        attendee we're fixing goes down, and the new score of the
        other attendee isn't greater than the unlucky attendee's new
        score (since that wouldn't be fair).

        Returns True if we swapped successfully, False otherwise.
        """
        attendees = (a for a in sorted(self.attendees.values(),
                                       key=lambda a: a.name)
                     if a != attendee)

        assigned_preferences = [p for p in reversed(attendee.preferences)
                                if p.assignment is not None]
        if len(assigned_preferences) == len(self.time_slots):
            if assigned_preferences[0].assignment.immutable:
                return False
            old_unlucky_score = attendee.score
            unassign_checkpoint = self.checkpoint()
            self.unassign(attendee, assigned_preferences[0].assignment.session)
        else:
            old_unlucky_score = None
            unassign_checkpoint = None

        # Just find anybody we can swap with.
        for other_attendee in attendees:
            for other_assignment in (p.assignment for p in
                                     reversed(other_attendee.preferences)
                                     if p.assignment is not None):
                # Can't unassign an immutable assignment.
                if other_assignment.immutable:
                    continue
                # This needs to be a topic the unlucky user actually wants
                # to attend and isn't already attending.
                if not any(p for p in attendee.preferences
                           if p.topic == other_assignment.session.topic and
                           not p.assigned):
                    continue
                # This assignment needs to be in a time-slot the unlucky
                # user has open.
                if any(p for p in attendee.preferences
                       if p.assignment is not None and
                       p.assignment.session.time_slot ==
                       other_assignment.session.time_slot):
                    continue
                checkpoint = self.checkpoint()
                self.unassign(other_attendee,
                              other_assignment.session)
                new_unlucky_score = attendee.score
                new_other_score = other_attendee.score
                if self.assign(attendee) and \
                   self.assign(other_attendee) and \
                   (old_unlucky_score is None or
                    (new_unlucky_score < old_unlucky_score and
                     new_other_score <= new_unlucky_score)):
                    self.commit(checkpoint)
                    if unassign_checkpoint is not None:
                        self.commit(unassign_checkpoint)
                    return True
                else:
                    self.rollback(checkpoint)

        if unassign_checkpoint is not None:
            self.rollback(unassign_checkpoint)

        return False


class NoMoreSpaceError(Exception):
    """Raised when an assignment would exceed the capacity of a session."""
    pass


class SlotConflictError(Exception):
    """Raised when an assignment would double-book an attendee."""
    pass


class ScheduleFailureError(Exception):
    """Raised when ``schedule()`` can't fill everyone's schedule."""
    pass


class Attendee(object):
    """Object representing event attendees.

    Generally speaking, a ``Scheduler`` object will create these for
    you; you shouldn't need to create them yourself, and in fact doing
    so will probably have unexpected results.

    Public properties
    -----------------

    ``name``
        Attendee's name.
    ``organization``
        Attendee's organization
    ``preferences``
        List of ``Preference`` objects reflecting the attendees
        preferred topics in preference order.
    ``max_assigned_preference``
        The index of the attendee's worst currently assigned
        preference. For example, if the attendee has five topic
        preferences, and the first, third, and fourth are assigned,
        then this property will return 3.
    ``num_assignments``
        How many of the attendee's preferences are currently assigned.
    ``score``
        The attendee's assignment score, which is defined as the sum
        of the indexes of all assigned preferences. A lower score is
        better.
    """

    def __init__(self, name, organization, topics):
        """
        ``name``
            Attendee's name.
        ``organization``
            Attendee's organization
        ``topics``
            The attendee's preferred topics, in preference
            order. These are ``Topic`` objects, not strings.
        """

        assert all(isinstance(t, Topic) for t in topics)

        self.name = name
        self.organization = organization
        self.preferences = [Preference(topic) for topic in topics]

    def __str__(self):
        return u'{} - {}'.format(self.organization, self.name)

    def dump(self):
        """Return a string representation of the state of the attendee."""

        o = unicode(self) + '\n'
        for preference in self.preferences:
            assignment = preference.assignment
            if assignment:
                o += u'  SESSION {}{}\n'.format(assignment.session,
                                                ' (immutable)' if
                                                assignment.immutable else '')
            else:
                o += u'  {}\n'.format(preference.topic)
        return o

    @property
    def max_assigned_preference(self):
        """Index of attendee's worst currently assigned preference."""

        return next(i for i in range(len(self.preferences) - 1, -1, -1)
                    if self.preferences[i].assigned)

    @property
    def num_assignments(self):
        """Number of currently assigned preferences."""

        return sum(1 for p in self.preferences if p.assignment is not None)

    @property
    def score(self):
        """Attendees assignment score."""

        return sum(i for i in range(len(self.preferences))
                   if self.preferences[i].assignment is not None)


class Assignment(object):
    """Object representing an assignment to a session.

    Generally speaking, a ``Scheduler`` object will create these for
    you; you shouldn't need to create them yourself, and in fact doing
    so will probably have unexpected results.

    Public properties
    -----------------

    ``session``
        ``Session`` object.
    ``immutable``
        Whether or not the assignment is immutable.
    """

    def __init__(self, session, immutable):
        self.session = session
        self.immutable = immutable


class Preference(object):
    """Object representing an attendee's topic preference.

    Generally speaking, a ``Scheduler`` object will create these for
    you; you shouldn't need to create them yourself, and in fact doing
    so will probably have unexpected results.

    Public properties
    -----------------

    ``topic``
        ``Topic`` object.
    ``assignment``
        ``Assignment`` object, if preference is assigned to a session.
    ``assigned``
        Whether or not preference is assigned. Equivalent to
        ``assignment is not None``.
    """

    def __init__(self, topic):
        self.topic = topic
        self.assignment = None

    def __str__(self):
        return unicode(self.topic)

    @property
    def assigned(self):
        return self.assignment is not None


class TimeSlot(object):
    """Object representing an event time-slot.

    Generally speaking, a ``Scheduler`` object will create these for
    you; you shouldn't need to create them yourself, and in fact doing
    so will probably have unexpected results.

    Public properties
    -----------------

    ``name``
        Time-slot name.
    ``session``
        List of sessions available during this time-slot.
    """

    def __init__(self, name):
        self.name = name
        self.sessions = []

    def add_session(self, session):
        if session in self.sessions:
            raise Exception('Duplicate session {} added to time-slot {}'.
                            format(session, self))
        self.sessions.append(session)

    def __str__(self):
        return unicode(self.name)


class Topic(object):
    """Object representing an event topic.

    Generally speaking, a ``Scheduler`` object will create these for
    you; you shouldn't need to create them yourself, and in fact doing
    so will probably have unexpected results.

    Public properties
    -----------------

    ``name``
        Topic name.
    ``sessions``
        Sessions available for this topic.
    """

    def __init__(self, name, time_slots):
        """
        Arguments
        ---------

        ``name``
            Topic name.
        ``time_slots``
            List of tuples. The first element of each tuple is a
            ``TimeSlot`` object indicating a time-slot in which a
            session for this topic will be held, and the second is the
            capacity (i.e., maximum number of attendees) for the
            session in that time-slot.
        """

        self.name = name

        assert all(isinstance(t[0], TimeSlot) and isinstance(t[1], int)
                   for t in time_slots)

        if len(time_slots) > len(set(t[0] for t in time_slots)):
            raise Exception('Duplicate time-slots specified for topic {} ('
                            'time-slots {})'.format(
                                self, [t[0] for t in time_slots]))

        self.sessions = [Session(self, t[0], t[1]) for t in time_slots]

    def __str__(self):
        return self.name

    def dump(self):
        o = self.name + '\n'
        for s in self.sessions:
            o += '  ' + s.dump()
        return o


class Session(object):
    """Object representing an event session.

    Generally speaking, a ``Scheduler`` object will create these for
    you; you shouldn't need to create them yourself, and in fact doing
    so will probably have unexpected results.

    A ``Session`` is a meeting of a particular topic during a
    particular time-slot.

    Public properties
    -----------------

    ``topic``
        ``Topic`` object.
    ``time_slot``
        ``TimeSlot`` object.
    ``capacity``
        Session capacity.
    ``attendees``
        List of ``Attendee`` objects.
    """

    def __init__(self, topic, time_slot, capacity):
        self.topic = topic
        self.time_slot = time_slot
        self.capacity = capacity
        self.time_slot.add_session(self)
        self.attendees = []

    def __str__(self):
        return u'{} - {}'.format(self.time_slot, self.topic)

    def dump(self):
        return u'Time slot {}, # of attendees {}, capacity {}\n'.format(
            self.time_slot, len(self.attendees), self.capacity)
