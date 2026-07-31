package com.sc.pesticideknowledgemappingsystem.repository.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.Crop;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideCropRelationship;
import org.springframework.data.neo4j.annotation.Depth;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PesticideCropRelationshipRepository extends Neo4jRepository<PesticideCropRelationship, Long> {
    @Query("MATCH (Pesticide:Pesticide)-[r:APPLIED_TO]->(Crop:Crop) " +
            "WHERE Pesticide.name = $pesticideName " +
            "RETURN Pesticide, Crop, r ")
    List<PesticideCropRelationship> findRelationshipsByPesticideName(@Param("pesticideName") String pesticideName);

    @Query("MATCH (Pesticide:Pesticide)-[r:APPLIED_TO]->(Crop:Crop) " +
            "WHERE Crop.name = $cropName " +
            "RETURN Pesticide, Crop, r ")
    List<PesticideCropRelationship> findRelationshipsBycropName(@Param("cropName") String cropName);

    @Query("MATCH (Pesticide:Pesticide {name: $pesticideName})-[r:APPLIED_TO]->(Crop:Crop {name: $cropName}) " +
            "RETURN Pesticide, Crop, r")
    PesticideCropRelationship findRelationshipsByPesticideNameAndCropName(@Param("pesticideName") String pesticideName, @Param("cropName") String cropName);

}