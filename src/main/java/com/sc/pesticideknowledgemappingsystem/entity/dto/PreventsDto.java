package com.sc.pesticideknowledgemappingsystem.entity.dto;

import com.sc.pesticideknowledgemappingsystem.entity.node.Disease;
import com.sc.pesticideknowledgemappingsystem.entity.node.Pesticide;
import lombok.Data;

@Data
public class PreventsDto {
    private Pesticide Pesticide; //杀虫剂节点
    private String relationship;
    private Disease Disease; //疾病节点
}
