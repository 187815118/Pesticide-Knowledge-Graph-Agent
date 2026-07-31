package com.sc.pesticideknowledgemappingsystem.repository.node;


import com.sc.pesticideknowledgemappingsystem.entity.node.PesticideCategory;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

//农药节点查询相关属性
@Repository
public interface PesticideCategoryRepository extends Neo4jRepository<PesticideCategory, Long> {

    PesticideCategory findByName(String name);
    List<PesticideCategory> findAll();

}