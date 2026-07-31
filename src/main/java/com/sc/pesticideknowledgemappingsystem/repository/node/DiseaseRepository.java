package com.sc.pesticideknowledgemappingsystem.repository.node;

import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DiseaseRepository extends Neo4jRepository<Disease, Long> {
    List<Disease> findByName(String name);
    List<Disease> findAll();
}
