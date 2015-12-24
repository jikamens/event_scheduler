NAME
    scheduler - Python Event Scheduler

DESCRIPTION
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

CLASSES
    class Scheduler(__builtin__.object)
     |  Main scheduling class
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``time_slots``
     |      Dictionary of name => ``TimeSlot`` objects, added with
     |      ``add_time_slot`` or ``add_time_slots``
     |  ``topics``
     |      Dictionary of name => ``Topic`` objects, added with
     |      ``add_topic``
     |  ``attendees``
     |      Dictionary of ``"{org} - {name}"`` => ``Attendee`` objects,
     |      added with ``add_attendee``
     |  
     |  Checkpointing
     |  -------------
     |  
     |  Checkpointing makes it easier to experiment with different
     |  scheduling options. You can checkpoint the current state of
     |  assignments at any time, rollback to the last checkpoint you
     |  created, or commit the last checkpoint you created. Once you
     |  rollback or commit a checkpoint, you can then rollback or commit
     |  the one before that, etc. To prevent programming errors, the
     |  checkpoint's name must be specified when committing or rolling
     |  back.
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |  
     |  add_attendee(self, name, organization, topics)
     |      Add an attendee.
     |      
     |      The combination of name and organization for attendees must be
     |      unique.
     |      
     |      ``topics`` is a list of topics in preference order. Topics can
     |      be specified as names or ``Topic`` objects.
     |  
     |  add_time_slot(self, name)
     |      Add a time slot.
     |      
     |      Time slot names must be unique.
     |  
     |  add_time_slots(self, names)
     |      Add multiple time slots at once.
     |  
     |  add_topic(self, name, time_slots)
     |      Add a topic.
     |      
     |      ``time_slots`` contains tuples of slot, capacity.
     |  
     |  assign(self, attendee, topic=None, immutable=False)
     |      Assign an attendee to their next best available topic session.
     |      
     |      Generally speaking, you will call ``schedule()`` rather than
     |      calling this method directly. One situation in which you might
     |      want to call this directly is if there a VIP attendee whom you
     |      want to schedule first to ensure they get their preferred
     |      topics.
     |      
     |      You can optionally specify a specific ``topic`` to which to
     |      assign the attendee.
     |      
     |      You can optionally specify that the assignment is
     |      ``immutable``, i.e., it should not be unassigned or modified
     |      once it is made.
     |      
     |      The logic for finding a session to which to assign the
     |      attendee is simple: the attendee is assigned a session for
     |      their highest-preference topic for which they haven't already
     |      been assigned a session and for which a session is available
     |      in a time-slot they have open.
     |      
     |      Returns True if a session was successfully assigned, or False
     |      otherwise.
     |  
     |  checkpoint(self, name=None)
     |      Checkpoint the scheduler state.
     |      
     |      If no name is specified, then a random name will be generated.
     |      
     |      The name of the new checkpoint is returned.
     |  
     |  clear_schedule(self, force=False)
     |      Clear all scheduling assignments.
     |      
     |      If ``force=True``, then also clear immutable assignments.
     |  
     |  commit(self, name)
     |      Commit the most recently created checkpoint.
     |      
     |      The checkpoint itself is removed after the changes are
     |      committed.
     |      
     |      To prevent programming errors, the name of the checkpoint
     |      being committed must be specified.
     |      
     |      Once a checkpoint is committed, it can't be rolled
     |      back. However, if there is an earlier checkpoint that has not
     |      yet been committed, the newly committed changes become part of
     |      *that* checkpoint and will be committed or rolled back with
     |      it.
     |  
     |  dump(self)
     |      Return a string representation of the state of the scheduler.
     |  
     |  manually_assign(self, attendee, topic)
     |      Manually assign an attendee to a session for a specific topic.
     |      
     |      The specified topic must appear in the attendee's preferences.
     |      
     |      Sessions assigned manually in this way are immutable, i.e.,
     |      the scheduling algorithm won't unassign or modify them.
     |      
     |      This is a convenience function that is equivalent to
     |      ``assign(attendee, topic=topic, immutable=True)``.
     |  
     |  rollback(self, name)
     |      Roll back the most recently created checkpoint.
     |      
     |      All changes since the checkpoint was created are undone, and
     |      the checkpoint is removed.
     |      
     |      To prevent programming errors, the name of the checkpoint
     |      being rolled back must be specified.
     |  
     |  schedule(self)
     |      Automatically schedule attendees in sessions.
     |      
     |      A best effort is made to schedule attendees to attend the
     |      topics they prefer.
     |      
     |      The scheduling algorithm as it is currently implemented is as
     |      follows:
     |      
     |      The first phase of scheduling is the time-slot phase, in which
     |      a pass is made through the attendees for each time-slot (e.g.,
     |      if there are three time-slots, then there will be three
     |      passes), and on each pass, an attempt is made to assign a
     |      session to each attendee whose schedule isn't already
     |      full. The time-slot phase works as follows:
     |      
     |      * Let n = number of passes in this phase
     |      * Let m = current pass of this phase, numbered from 0
     |      * Sort attendees by the sum of their top (n - m) unassigned
     |        preferences, then in reverse order by the sum of their
     |        position in prior passes, then by ``"{org} - {name}"`` for
     |        stability.
     |      * Skip attendees whose schedules are already full.
     |      * Try to assign a session to each attendee (see the
     |        documentation for the ``assign`` method).
     |      
     |      Next is the fill phase, in which we attempt to fill attendee
     |      schedules that aren't currently filled because the order in
     |      which sessions were assigned prevented us from assigning
     |      sessions for some attendees in some passes. See the
     |      documentation for the ``swap`` method for details on how this
     |      is done.
     |      
     |      Finally is the improve phase, where we attempt to move around
     |      assignments to improve the overall happiness of
     |      attendees. Again, see ``swap`` for additional details.
     |      
     |      Note that this algorithm and implementation don't try to
     |      create a "perfect" or "optimal" schedule. That's actually a
     |      pretty hard problem and I'm frankly not sure it's worth the
     |      effort. The goal is to make reasonably good assignments.
     |  
     |  swap(self, attendee)
     |      Try to improve the schedule for an attendee.
     |      
     |      The specified attendee (the "unlucky" attendee) needs
     |      improvement either because he doesn't have all of his
     |      assignments, or because he didn't get his top preferences and
     |      we want to see if we can move people around to make things
     |      more fair.
     |      
     |      In the former case, we're willing to steal any assignment from
     |      any other attendee that enables us to fill both attendees'
     |      sessions.
     |      
     |      In the latter case, we calculate the score of the unlucky
     |      attendee -- defined as the sum of the preferences he was
     |      successfully assigned, which obviously means that a lower
     |      score is better from the point of view of the attendee -- then
     |      we unassign the worst-assigned preference from the unlucky
     |      attendee and try to find another attendee we can steal an
     |      assignment from such that the new score of the unlucky
     |      attendee we're fixing goes down, and the new score of the
     |      other attendee isn't greater than the unlucky attendee's new
     |      score (since that wouldn't be fair).
     |      
     |      Returns True if we swapped successfully, False otherwise.
     |  
     |  unassign(self, attendee, session, force=False)
     |      Unassigned an attendee from a session.
     |      
     |      Won't modify an immutable assignment without ``force=True``.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Attendee(__builtin__.object)
     |  Object representing event attendees.
     |  
     |  Generally speaking, a ``Scheduler`` object will create these for
     |  you; you shouldn't need to create them yourself, and in fact doing
     |  so will probably have unexpected results.
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``name``
     |      Attendee's name.
     |  ``organization``
     |      Attendee's organization
     |  ``preferences``
     |      List of ``Preference`` objects reflecting the attendees
     |      preferred topics in preference order.
     |  ``max_assigned_preference``
     |      The index of the attendee's worst currently assigned
     |      preference. For example, if the attendee has five topic
     |      preferences, and the first, third, and fourth are assigned,
     |      then this property will return 3.
     |  ``num_assignments``
     |      How many of the attendee's preferences are currently assigned.
     |  ``score``
     |      The attendee's assignment score, which is defined as the sum
     |      of the indexes of all assigned preferences. A lower score is
     |      better.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, name, organization, topics)
     |      ``name``
     |          Attendee's name.
     |      ``organization``
     |          Attendee's organization
     |      ``topics``
     |          The attendee's preferred topics, in preference
     |          order. These are ``Topic`` objects, not strings.
     |  
     |  __str__(self)
     |  
     |  dump(self)
     |      Return a string representation of the state of the attendee.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  max_assigned_preference
     |      Index of attendee's worst currently assigned preference.
     |  
     |  num_assignments
     |      Number of currently assigned preferences.
     |  
     |  score
     |      Attendees assignment score.
    
    class Assignment(__builtin__.object)
     |  Object representing an assignment to a session.
     |  
     |  Generally speaking, a ``Scheduler`` object will create these for
     |  you; you shouldn't need to create them yourself, and in fact doing
     |  so will probably have unexpected results.
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``session``
     |      ``Session`` object.
     |  ``immutable``
     |      Whether or not the assignment is immutable.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, session, immutable)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Preference(__builtin__.object)
     |  Object representing an attendee's topic preference.
     |  
     |  Generally speaking, a ``Scheduler`` object will create these for
     |  you; you shouldn't need to create them yourself, and in fact doing
     |  so will probably have unexpected results.
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``topic``
     |      ``Topic`` object.
     |  ``assignment``
     |      ``Assignment`` object, if preference is assigned to a session.
     |  ``assigned``
     |      Whether or not preference is assigned. Equivalent to
     |      ``assignment is not None``.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, topic)
     |  
     |  __str__(self)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  assigned
    
    class Session(__builtin__.object)
     |  Object representing an event session.
     |  
     |  Generally speaking, a ``Scheduler`` object will create these for
     |  you; you shouldn't need to create them yourself, and in fact doing
     |  so will probably have unexpected results.
     |  
     |  A ``Session`` is a meeting of a particular topic during a
     |  particular time-slot.
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``topic``
     |      ``Topic`` object.
     |  ``time_slot``
     |      ``TimeSlot`` object.
     |  ``capacity``
     |      Session capacity.
     |  ``attendees``
     |      List of ``Attendee`` objects.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, topic, time_slot, capacity)
     |  
     |  __str__(self)
     |  
     |  dump(self)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class TimeSlot(__builtin__.object)
     |  Object representing an event time-slot.
     |  
     |  Generally speaking, a ``Scheduler`` object will create these for
     |  you; you shouldn't need to create them yourself, and in fact doing
     |  so will probably have unexpected results.
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``name``
     |      Time-slot name.
     |  ``session``
     |      List of sessions available during this time-slot.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, name)
     |  
     |  __str__(self)
     |  
     |  add_session(self, session)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Topic(__builtin__.object)
     |  Object representing an event topic.
     |  
     |  Generally speaking, a ``Scheduler`` object will create these for
     |  you; you shouldn't need to create them yourself, and in fact doing
     |  so will probably have unexpected results.
     |  
     |  Public properties
     |  -----------------
     |  
     |  ``name``
     |      Topic name.
     |  ``sessions``
     |      Sessions available for this topic.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, name, time_slots)
     |      Arguments
     |      ---------
     |      
     |      ``name``
     |          Topic name.
     |      ``time_slots``
     |          List of tuples. The first element of each tuple is a
     |          ``TimeSlot`` object indicating a time-slot in which a
     |          session for this topic will be held, and the second is the
     |          capacity (i.e., maximum number of attendees) for the
     |          session in that time-slot.
     |  
     |  __str__(self)
     |  
     |  dump(self)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)


