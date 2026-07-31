package com.sc.pesticideknowledgemappingsystem.repository.node;

import com.sc.pesticideknowledgemappingsystem.entity.node.ChemicalClasses;
import com.sc.pesticideknowledgemappingsystem.entity.node.Crop;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CropRepository extends Neo4jRepository<Crop, Long> {
    Crop findByName(String name);

    List<Crop> findAll();
}


