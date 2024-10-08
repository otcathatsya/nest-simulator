/*
 *  connection_manager_impl.h
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

#ifndef CONNECTION_MANAGER_IMPL_H
#define CONNECTION_MANAGER_IMPL_H

#include "connection_manager.h"

// C++ includes:
#include <string>

// Includes from nestkernel:
#include "conn_builder.h"
#include "conn_builder_factory.h"
#include "connector_base.h"
#include "kernel_manager.h"
#include "target_table_devices_impl.h"

namespace nest
{

template < typename ConnBuilder >
void
ConnectionManager::register_conn_builder( const std::string& name )
{
  assert( not connruledict_->known( name ) );
  GenericBipartiteConnBuilderFactory* cb = new BipartiteConnBuilderFactory< ConnBuilder >();
  assert( cb );
  const int id = connbuilder_factories_.size();
  connbuilder_factories_.push_back( cb );
  connruledict_->insert( name, id );
}

template < typename ThirdConnBuilder >
void
ConnectionManager::register_third_conn_builder( const std::string& name )
{
  assert( not thirdconnruledict_->known( name ) );
  GenericThirdConnBuilderFactory* cb = new ThirdConnBuilderFactory< ThirdConnBuilder >();
  assert( cb );
  const int id = thirdconnbuilder_factories_.size();
  thirdconnbuilder_factories_.push_back( cb );
  thirdconnruledict_->insert( name, id );
}

inline void
ConnectionManager::send_to_devices( const size_t tid, const size_t source_node_id, Event& e )
{
  target_table_devices_.send_to_device( tid, source_node_id, e, kernel().model_manager.get_connection_models( tid ) );
}

inline void
ConnectionManager::send_to_devices( const size_t tid, const size_t source_node_id, SecondaryEvent& e )
{
  target_table_devices_.send_to_device( tid, source_node_id, e, kernel().model_manager.get_connection_models( tid ) );
}

inline void
ConnectionManager::send_from_device( const size_t tid, const size_t ldid, Event& e )
{
  target_table_devices_.send_from_device( tid, ldid, e, kernel().model_manager.get_connection_models( tid ) );
}

} // namespace nest

#endif /* CONNECTION_MANAGER_IMPL_H */
