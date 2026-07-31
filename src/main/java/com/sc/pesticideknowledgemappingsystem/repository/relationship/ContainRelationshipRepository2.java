package com.sc.pesticideknowledgemappingsystem.repository.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.relationship.ContainRelationship2;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ContainRelationshipRepository2 extends Neo4jRepository<ContainRelationship2, Long> {

    @Query("MATCH (n:ChemicalClasses {name: $chemicalClassesName})-[r:INCLUDES]->(m:ActiveSubstance) RETURN n,m,r")
    List<ContainRelationship2> findRelationshipsByChemicalClassesName(@Param("chemicalClassesName") String chemicalClassesName);

    /**
     * 根据具体类型名查询关系2
     *
     * @param activeSubstanceName 活性物质名
     * @return 包含关系2的实体对象
     */
    @Query("MATCH p=()-[r:INCLUDES]->(activeSubstance:ActiveSubstance {name: $activeSubstanceName}) RETURN p LIMIT 25")
    List<ContainRelationship2> findRelationshipsByActiveSubstanceName(@Param("activeSubstanceName") String activeSubstanceName);

    @Query("MATCH (chemicalClasses:ChemicalClasses {name: $chemicalClassesName})-[r:INCLUDES]->(activeSubstance:ActiveSubstance {name: $activeSubstanceName}) " +
            "RETURN chemicalClasses, activeSubstance, r")
        /*根据结构类别名和具体类型名查询关系2*/
    ContainRelationship2 findRelationshipsByChemicalClassesNameAndActiveSubstanceName(@Param("chemicalClassesName") String chemicalClassesName, @Param("activeSubstanceName") String activeSubstanceName);
}