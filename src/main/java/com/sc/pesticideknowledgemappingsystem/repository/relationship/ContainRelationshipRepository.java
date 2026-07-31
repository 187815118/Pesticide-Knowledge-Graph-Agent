package com.sc.pesticideknowledgemappingsystem.repository.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.*;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.ContainRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.DiseaseRelationship;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ContainRelationshipRepository extends Neo4jRepository<ContainRelationship, Long> {

    //通过农药类别来查询所包含的结构类别
    @Query("MATCH (pesticideCategory:PesticideCategory {name: $pesticideCategoryName})-[r:INCLUDES]->(chemicalClasses:ChemicalClasses) " +
            "RETURN pesticideCategory, chemicalClasses, r")
    List<ContainRelationship> findRelationshipsPesticideCategoryName(@Param("pesticideCategoryName") String pesticideCategoryName);
    /**
     * 根据结构类别名查询关系1
     *
     * @param chemicalClassesName 结构类别名
     * @return 包含关系1的实体对象
     */

    //查询指定结构类别
    @Query("MATCH p=()-[r:INCLUDES]->(ChemicalClassesNode:ChemicalClasses {name: $chemicalClassName}) RETURN p LIMIT 25")
    List<ContainRelationship> findRelationshipsByChemicalClassesName(@Param("chemicalClassName") String chemicalClassesName);


    @Query("MATCH (PesticideCategory:PesticideCategory {name: $pesticideCategory})-[r:INCLUDES]->(ChemicalClasses:ChemicalClasses {name: $chemicalClassName}) " +
            "RETURN PesticideCategory, ChemicalClasses, r")
    /*根据农药大类名和结构类别名查询关系1*/
    ContainRelationship findRelationshipsByPesticideCategoryAndChemicalClasses(@Param("pesticideCategory") String pesticideCategory, @Param("chemicalClassName") String chemicalClassName);

    //作用位点作用作用模式
    @Query("MATCH (targetSite:TargetSite {name: $targetSite})-[r:DETERMINES]->(modeOfAction:ModeOfAction {name: $modeOfAction}) " +
            "RETURN targetSite, modeOfAction, r")
    ContainRelationship findByModeOfActionAndChemicalClasses(@Param("targetSite") String targetSite, @Param("modeOfAction") String modeOfAction);
}