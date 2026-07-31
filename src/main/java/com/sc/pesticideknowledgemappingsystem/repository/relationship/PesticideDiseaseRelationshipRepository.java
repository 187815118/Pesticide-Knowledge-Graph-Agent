package com.sc.pesticideknowledgemappingsystem.repository.relationship;

import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideCropRelationship;
import com.sc.pesticideknowledgemappingsystem.entity.relationship.PesticideDiseaseRelationship;
import org.springframework.data.neo4j.annotation.Query;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PesticideDiseaseRelationshipRepository extends Neo4jRepository<PesticideDiseaseRelationship, Long> {

    @Query("MATCH (n:Pesticide)-[r:TREATS]->(m:Disease {name: $diseaseName}) RETURN n, m, r")
    List<PesticideDiseaseRelationship> findByDiseaseName(@Param("diseaseName") String diseaseName);

    /*根据农药名查询关系*/
    @Query("MATCH (Pesticide:Pesticide)-[r:TREATS]->(Disease:Disease) " +
            "WHERE Pesticide.name = $pesticideName " +
            "RETURN Pesticide, Disease, r ")
    List<PesticideDiseaseRelationship> findRelationshipsByPesticideName(@Param("pesticideName") String pesticideName);

    @Query("MATCH (Pesticide:Pesticide {name: $pesticideName})-[r:TREATS]->(Disease:Disease {name: $diseaseName}) " +
            "RETURN Pesticide, Disease, r")
    PesticideDiseaseRelationship findRelationshipsByPesticideNameAndDiseaseName(@Param("pesticideName") String pesticideName, @Param("diseaseName") String diseaseName);

    @Query("MATCH (p:Pesticide)-[r:TREATS]->(d:Disease) " +
            "WHERE p.name = $pesticideName AND d.name = $diseaseName " +
            "RETURN p, r, d " +
            "LIMIT 25")
    PesticideDiseaseRelationship findByPesticideNameAndDiseaseName(@Param("pesticideName") String pesticideName, @Param("diseaseName") String diseaseName);
    //@Query("p:s")
    //PesticideDiseaseRelationship findByPesticideNameAndDiseaseName(@Param("s") String s);

}