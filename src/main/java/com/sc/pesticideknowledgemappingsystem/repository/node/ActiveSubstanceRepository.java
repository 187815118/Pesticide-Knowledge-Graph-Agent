package com.sc.pesticideknowledgemappingsystem.repository.node;

import com.sc.pesticideknowledgemappingsystem.entity.node.ActiveSubstance;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ActiveSubstanceRepository extends Neo4jRepository<ActiveSubstance, Long> {
    List<ActiveSubstance> findAll();

    ActiveSubstance findByName(String name);
}


