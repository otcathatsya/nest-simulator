/*
 *  stopwatch.h
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#ifndef STOPWATCH_H
#define STOPWATCH_H

// C includes:
#include <sys/time.h>

// C++ includes:
#include "arraydatum.h"
#include "dictdatum.h"
#include "dictutils.h"
#include <algorithm>
#include <cassert>
#include <chrono>
#include <iostream>
#include <vector>

namespace nest
{

// TODO JV: Set this variable via cmake instead
#ifdef TIMER_DETAILED
constexpr bool use_detailed_timers = true;
#else
constexpr bool use_detailed_timers = false;
#endif
#ifdef THREADED_TIMERS
constexpr bool use_threaded_timers = true;
#else
constexpr bool use_threaded_timers = false;
#endif

/********************************************************************************
 * Stopwatch                                                                    *
 *   Accumulates time between start and stop, and provides the elapsed time     *
 *   with different time units. Either runs multi-threaded or only on master.   *
 *                                                                              *
 *   Usage example:                                                             *
 *     Stopwatch< StopwatchVerbosity::Normal, StopwatchType::MasterOnly > x;    *
 *     x.start();                                                               *
 *     // ... do computations for 15.34 sec                                     *
 *     x.stop(); // only pauses stopwatch                                       *
 *     x.print("Time needed "); // > Time needed 15.34 sec.                     *
 *     x.start(); // resumes stopwatch                                          *
 *     // ... next computations for 11.22 sec                                   *
 *     x.stop();                                                                *
 *     x.print("Time needed "); // > Time needed 26,56 sec.                     *
 *     x.reset(); // reset to default values                                    *
 *     x.start(); // starts the stopwatch from 0                                *
 *     // ... computation 5.7 sec                                               *
 *     x.print("Time "); // > Time 5.7 sec.                                     *
 *     // ^ intermediate timing without stopping the stopwatch                  *
 *     // ... more computations 1.7643 min                                      *
 *     x.stop();                                                                *
 *     x.print("Time needed ", StopwatchBase< clock_type >::MINUTES, std::cerr);              *
 *     // > Time needed 1,8593 min. (on cerr)                                   *
 *     // other units and output streams possible                               *
 ********************************************************************************/
namespace timers
{
enum timeunit_t : size_t
{
  NANOSEC = 1,
  MICROSEC = NANOSEC * 1000,
  MILLISEC = MICROSEC * 1000,
  SECONDS = MILLISEC * 1000,
  MINUTES = SECONDS * 60,
  HOURS = MINUTES * 60,
  DAYS = HOURS * 24
};

template < size_t clock_type >
class StopwatchBase
{
public:
  typedef size_t timestamp_t;

  /**
   * Creates a stopwatch that is not running.
   */
  StopwatchBase()
  {
    reset();
  }

  /**
   * Starts or resumes the stopwatch, if it is not running already.
   */
  void start();

  /**
   * Stops the stopwatch, if it is not stopped already.
   */
  void stop();

  /**
   * Returns, whether the stopwatch is running.
   */
  bool isRunning() const;

  /**
   * Returns the time elapsed between the start and stop of the stopwatch in the given unit. If it is running, it
   * returns the time from start until now. If the stopwatch is run previously, the previous runtime is added. If you
   * want only the last measurement, you have to reset the timer, before stating the measurement.
   * Does not change the running state.
   */
  double elapsed( timeunit_t timeunit = SECONDS ) const;

  /**
   * Resets the stopwatch.
   */
  void reset();

  /**
   * This method prints out the currently elapsed time.
   */
  void print( const char* msg = "", timeunit_t timeunit = SECONDS, std::ostream& os = std::cout ) const;

  /**
   * Convenient method for writing time in seconds
   * to some ostream.
   */
  // friend std::ostream& operator<<( std::ostream& os, const StopwatchBase< clock_type >& stopwatch );

private:
#ifndef DISABLE_TIMING
  timestamp_t _beg, _end;
  size_t _prev_elapsed;
  bool _running;
#endif

  /**
   * Returns current time in microseconds since EPOCH.
   */
  static size_t get_current_time();
};

template < size_t clock_type >
inline void
StopwatchBase< clock_type >::start()
{
#ifndef DISABLE_TIMING
  if ( not isRunning() )
  {
    _prev_elapsed += _end - _beg;     // store prev. time, if we resume
    _end = _beg = get_current_time(); // invariant: _end >= _beg
    _running = true;                  // we start running
  }
#endif
}

template < size_t clock_type >
inline void
StopwatchBase< clock_type >::stop()
{
#ifndef DISABLE_TIMING
  if ( isRunning() )
  {
    _end = get_current_time(); // invariant: _end >= _beg
    _running = false;          // we stopped running
  }
#endif
}

template < size_t clock_type >
inline bool
StopwatchBase< clock_type >::isRunning() const
{
#ifndef DISABLE_TIMING
  return _running;
#else
  return false;
#endif
}

template < size_t clock_type >
inline double
StopwatchBase< clock_type >::elapsed( timeunit_t timeunit ) const
{
#ifndef DISABLE_TIMING
  size_t time_elapsed;
  if ( isRunning() )
  {
    // get intermediate elapsed time; do not change _end, to be const
    time_elapsed = get_current_time() - _beg + _prev_elapsed;
  }
  else
  {
    // stopped before, get time of current measurement + last measurements
    time_elapsed = _end - _beg + _prev_elapsed;
  }
  return static_cast< double >( time_elapsed ) / timeunit;
#else
  return 0.;
#endif
}

template < size_t clock_type >
inline void
StopwatchBase< clock_type >::reset()
{
#ifndef DISABLE_TIMING
  _beg = 0; // invariant: _end >= _beg
  _end = 0;
  _prev_elapsed = 0; // erase all prev. measurements
  _running = false;  // of course not running.
#endif
}

template < size_t clock_type >
inline void
StopwatchBase< clock_type >::print( const char* msg, timeunit_t timeunit, std::ostream& os ) const
{
#ifndef DISABLE_TIMING
  double e = elapsed( timeunit );
  os << msg << e;
  switch ( timeunit )
  {
  case MICROSEC:
    os << " microsec.";
    break;
  case MILLISEC:
    os << " millisec.";
    break;
  case SECONDS:
    os << " sec.";
    break;
  case MINUTES:
    os << " min.";
    break;
  case HOURS:
    os << " h.";
    break;
  case DAYS:
    os << " days.";
    break;
  }
#ifdef DEBUG
  os << " (running: " << ( _running ? "true" : "false" ) << ", begin: " << _beg << ", end: " << _end
     << ", diff: " << ( _end - _beg ) << ", prev: " << _prev_elapsed << ")";
#endif
  os << std::endl;
#endif
}

template < size_t clock_type >
inline size_t
StopwatchBase< clock_type >::get_current_time()
{
  // We use a monotonic timer to make sure the stopwatch is not influenced by time jumps (e.g. summer/winter time).
  timespec now;
  clock_gettime( clock_type, &now );
  return now.tv_nsec + now.tv_sec * timeunit_t::SECONDS;
}

/*template< size_t clock_type >
inline std::ostream&
operator<<( std::ostream& os, const StopwatchBase< clock_type >& stopwatch )
{
  stopwatch.print( "", timeunit_t::SECONDS, os );
  return os;
}*/

}

enum StopwatchVerbosity
{
  Normal,  //<! Always measure stopwatch
  Detailed //<! Only measure if detailed stopwatches are activated
};

enum StopwatchType
{
  MasterOnly, //<! Only the master thread owns a stopwatch
  Threaded    //<! Every thread measures an individual stopwatch
};


/** This is the base template for all Stopwatch specializations.
 */
/** Base timer class, which only measures a single timer, owned by the master thread. Might only actually measure time
 * if detailed timers are enabled.
 */
template < StopwatchVerbosity detailed_timer, StopwatchType threaded_timer, typename = void >
class Stopwatch
{
public:
  void
  start()
  {
#pragma omp master
    {
      walltime_timer_.start();
      cputime_timer_.start();
    }
  }

  void
  stop()
  {
#pragma omp master
    {
      walltime_timer_.stop();
      cputime_timer_.stop();
    }
  }

  bool
  isRunning() const
  {
    bool isRunning = false;
#pragma omp master
    {
      isRunning = walltime_timer_.isRunning();
    };
    return isRunning;
  }

  double
  elapsed( timers::timeunit_t timeunit = timers::timeunit_t::SECONDS ) const
  {
    double elapsed = 0.;
#pragma omp master
    {
      elapsed = walltime_timer_.elapsed( timeunit );
    };
    return elapsed;
  }

  void
  reset()
  {
#pragma omp master
    {
      walltime_timer_.reset();
      cputime_timer_.reset();
    }
  }

  void
  print( const char* msg = "",
    timers::timeunit_t timeunit = timers::timeunit_t::SECONDS,
    std::ostream& os = std::cout ) const
  {
#pragma omp master
    walltime_timer_.print( msg, timeunit, os );
  }

  void
  output_timer( DictionaryDatum& d, const Name& walltime_name, const Name& cputime_name )
  {
    def< double >( d, walltime_name, walltime_timer_.elapsed() );
    def< double >( d, cputime_name, cputime_timer_.elapsed() );
  }

private:
  timers::StopwatchBase< CLOCK_MONOTONIC > walltime_timer_;
  timers::StopwatchBase< CLOCK_THREAD_CPUTIME_ID > cputime_timer_;
};

/** If the user deactivated detailed timers, Stopwatch instance with the detailed flag will become an empty Stopwatch,
 * which will be safely ignored by the compiler, as if the instance was not declared (e.g. as a member).
 */
template <>
class Stopwatch< StopwatchVerbosity::Detailed, StopwatchType::MasterOnly, std::enable_if< not use_detailed_timers > >
{
public:
  void
  start()
  {
  }
  void
  stop()
  {
  }
  bool
  isRunning() const
  {
    return false;
  }
  double
  elapsed( timers::timeunit_t = timers::timeunit_t::SECONDS ) const
  {
    return 0;
  }
  void
  reset()
  {
  }
  void
  print( const char* = "", timers::timeunit_t = timers::timeunit_t::SECONDS, std::ostream& = std::cout ) const
  {
  }
  void
  output_timer( DictionaryDatum&, const Name&, const Name& )
  {
  }
};

/** Only provide these template specializations if threaded timers are activated and always fall back to the base
 * template specialization if not. Deactivate threaded detailed timers if all detailed timers are deactivated.
 */
template < StopwatchVerbosity detailed_timer >
class Stopwatch< detailed_timer,
  StopwatchType::Threaded,
  std::enable_if_t< use_threaded_timers
    and ( detailed_timer == StopwatchVerbosity::Detailed and not use_detailed_timers ) > >
{
public:
  void
  start()
  {
  }
  void
  stop()
  {
  }
  bool
  isRunning() const
  {
    return false;
  }
  double
  elapsed( timers::timeunit_t = timers::timeunit_t::SECONDS ) const
  {
    return 0;
  }
  void
  reset()
  {
  }
  void
  print( const char* = "", timers::timeunit_t = timers::timeunit_t::SECONDS, std::ostream& = std::cout ) const
  {
  }
  void
  output_timer( DictionaryDatum&, const Name&, const Name& )
  {
  }
};
template < StopwatchVerbosity detailed_timer >
class Stopwatch< detailed_timer,
  StopwatchType::Threaded,
  std::enable_if_t< use_threaded_timers and ( detailed_timer == StopwatchVerbosity::Normal or use_detailed_timers ) > >
{
public:
  void start();

  void stop();

  bool isRunning() const;

  double elapsed( timers::timeunit_t timeunit = timers::timeunit_t::SECONDS ) const;

  void reset();

  void print( const char* msg = "",
    timers::timeunit_t timeunit = timers::timeunit_t::SECONDS,
    std::ostream& os = std::cout ) const;

  void
  output_timer( DictionaryDatum& d, const Name& walltime_name, const Name& cputime_name )
  {
    std::vector< double > wall_times( walltime_timers_.size() );
    std::transform( walltime_timers_.begin(),
      walltime_timers_.end(),
      wall_times.begin(),
      []( const timers::StopwatchBase< CLOCK_MONOTONIC >& timer ) { return timer.elapsed(); } );
    def< ArrayDatum >( d, walltime_name, ArrayDatum( wall_times ) );
    std::vector< double > cpu_times( cputime_timers_.size() );
    std::transform( cputime_timers_.begin(),
      cputime_timers_.end(),
      cpu_times.begin(),
      []( const timers::StopwatchBase< CLOCK_THREAD_CPUTIME_ID >& timer ) { return timer.elapsed(); } );
    def< ArrayDatum >( d, cputime_name, ArrayDatum( cpu_times ) );
  }

private:
  std::vector< timers::StopwatchBase< CLOCK_MONOTONIC > > walltime_timers_;
  std::vector< timers::StopwatchBase< CLOCK_THREAD_CPUTIME_ID > > cputime_timers_;
};

} /* namespace timer */
#endif /* STOPWATCH_H */
