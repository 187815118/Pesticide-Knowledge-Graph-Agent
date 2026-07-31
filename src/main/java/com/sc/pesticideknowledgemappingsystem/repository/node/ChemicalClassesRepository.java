package com.sc.pesticideknowledgemappingsystem.repository.node;

import com.sc.pesticideknowledgemappingsystem.entity.node.ChemicalClasses;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ChemicalClassesRepository extends Neo4jRepository<ChemicalClasses, Long> {
    ChemicalClasses findByName(String name);

    List<ChemicalClasses> findAll();
}