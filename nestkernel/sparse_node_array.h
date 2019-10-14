/*
 *  sparse_node_array.h
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

#ifndef SPARSE_NODE_ARRAY_H
#define SPARSE_NODE_ARRAY_H

// C++ includes:
#include <cassert>
#include <map>

// Includes from nestkernel:
#include "nest_types.h"

// Includes from libnestutil
#include "block_vector.h"


namespace nest
{
class Node;

/**
 * Provide sparse representation of local nodes.
 *
 * This class is a container providing lookup of local nodes (as Node*)
 * based on GIDs.
 *
 * Basically, this array is a vector containing only pointers to local nodes.
 * For M MPI processes, we have
 *
 *   GID  %  M  --> rank
 *   GID div M  --> index on rank
 *
 * so that the latter gives and index into the local node array. This index
 * will be skewed due to nodes without proxies present on all ranks, whence
 * computation may give an index that is too low and we must search to the right
 * for the actual node. We never need to search to the left.
 */
class SparseNodeArray
{
public:
  struct NodeEntry
  {
    NodeEntry() = default;
    NodeEntry( Node&, index );

    // Accessor functions here are mostly in place to make things "look nice".
    // Since SparseNodeArray only exposes access to const_interator, iterators
    // could anyways not be used to change entry contents.
    // TODO: But we may want to re-think this.
    Node* get_node() const;
    index get_gid() const;

    Node* node_;
    index gid_; //!< store gid locally for faster searching
  };

  typedef BlockVector< SparseNodeArray::NodeEntry >::const_iterator const_iterator;

  //! Create empty spare node array
  SparseNodeArray();

  /**
   * Return size of container.
   * @see get_max_gid()
   */
  size_t size() const;

  //! Clear the array
  void clear();

  /**
   * Add single local node.
   */
  void add_local_node( Node& );

  /**
   * Set max gid to max in network.
   *
   * Ensures that array knows about non-local nodes
   * with GIDs higher than highest local GID.
   */
  void update_max_gid( index );

  /**
   *  Lookup node based on GID
   *
   *  Returns 0 if GID is not local.
   *
   *  The caller is responsible for providing proper
   *  proxy node pointers for non-local nodes
   *
   *  @see get_node_by_index()
   */
  Node* get_node_by_gid( index ) const;

  /**
   * Lookup node based on index into container.
   *
   * Use this when you need to iterate over local nodes only.
   *
   * @see get_node_by_gid()
   */
  Node* get_node_by_index( size_t ) const;

  /**
   * Get constant iterators for safe iteration of SparseNodeArray.
   */
  const_iterator begin() const;
  const_iterator end() const;

  /**
   * Return largest GID in global network.
   * @see size
   */
  index get_max_gid() const;

private:
  BlockVector< NodeEntry > nodes_; //!< stores local node information
  index max_gid_;                  //!< largest GID in network
  index local_min_gid_;            //!< smallest local GID
  index local_max_gid_;            //!< largest local GID
  double gid_idx_scale_;           //!< interpolation factor
};

} // namespace nest

inline nest::SparseNodeArray::const_iterator
nest::SparseNodeArray::begin() const
{
  return nodes_.begin();
}

inline nest::SparseNodeArray::const_iterator
nest::SparseNodeArray::end() const
{
  return nodes_.end();
}

inline size_t
nest::SparseNodeArray::size() const
{
  return nodes_.size();
}

inline void
nest::SparseNodeArray::clear()
{
  nodes_.clear();
  max_gid_ = 0;
  local_min_gid_ = 0;
  local_max_gid_ = 0;
  gid_idx_scale_ = 1.;
}

inline nest::Node*
nest::SparseNodeArray::get_node_by_index( size_t idx ) const
{
  assert( idx < nodes_.size() );
  return nodes_[ idx ].node_;
}

inline nest::index
nest::SparseNodeArray::get_max_gid() const
{
  return max_gid_;
}

inline nest::Node*
nest::SparseNodeArray::NodeEntry::get_node() const
{
  return node_;
}

inline nest::index
nest::SparseNodeArray::NodeEntry::get_gid() const
{
  return gid_;
}

#endif /* SPARSE_NODE_ARRAY_H */
