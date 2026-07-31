package com.sc.pesticideknowledgemappingsystem.repository.node;

import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

//农药节点查询相关属性
@Repository
public interface PesticideRepository extends Neo4jRepository<Pesticide, Long> {
    List<Pesticide> findByPesticideCategory(String pesticideCategory);//该农药属于的农药大类,杀虫剂，杀菌剂这些

    Pesticide findByName(String name);

}