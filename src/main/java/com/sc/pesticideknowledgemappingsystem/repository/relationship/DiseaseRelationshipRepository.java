package com.sc.pesticideknowledgemappingsystem.repository.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.Crop;
import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.DiseaseRelationship;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DiseaseRelationshipRepository extends Neo4jRepository<DiseaseRelationship, Long> {
    /*根据作物名查询致病关系*/
    @Query("MATCH (n:Disease)-[r:INFECTS]->(m:Crop {name: $cropName}) RETURN n, m, r")
    List<DiseaseRelationship> findRelationshipsByCropName(@Param("cropName") String cropName);

    /*根据病害名查询致病关系*/
    @Query("MATCH (n:Disease {name: $diseaseName})-[r:INFECTS]->(m:Crop) RETURN n, m, r")
    List<DiseaseRelationship> findRelationshipsByDiseaseName(@Param("diseaseName") String diseaseName);

    @Query("MATCH (Disease:Disease {name: $diseaseName})-[r:INFECTS]->(Crop:Crop {name: $cropName}) " +
            "RETURN Disease, Crop, r")
    DiseaseRelationship findRelationshipsByDiseaseNameAndCropName(@Param("diseaseName") String diseaseName, @Param("cropName") String cropName);
}