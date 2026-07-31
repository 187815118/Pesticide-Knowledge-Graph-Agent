package com.sc.pesticideknowledgemappingsystem.repository.node;


import com.sc.pesticideknowledgemappingsystem.entity.node.*;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

//农药节点查询相关属性
@Repository
public interface TargetSiteRepository extends Neo4jRepository<TargetSite, Long> {

    TargetSite findByName(String name);
    List<TargetSite> findAll();

}