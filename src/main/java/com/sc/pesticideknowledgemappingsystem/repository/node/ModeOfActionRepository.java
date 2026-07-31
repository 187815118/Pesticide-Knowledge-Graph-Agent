package com.sc.pesticideknowledgemappingsystem.repository.node;

import com.sc.pesticideknowledgemappingsystem.entity.node.ModeOfAction;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

//接口定义了一些用于操作 Neo4j 数据库中 ModeOfAction 节点的方法，比如根据名称查找节点，以及获取所有节点。
@Repository
public interface ModeOfActionRepository extends Neo4jRepository<ModeOfAction, Long> {
    List<ModeOfAction> findAll();
    ModeOfAction findByName(String name);
}