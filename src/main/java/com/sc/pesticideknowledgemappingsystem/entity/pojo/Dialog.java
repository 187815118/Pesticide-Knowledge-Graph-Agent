package com.sc.pesticideknowledgemappingsystem.entity.pojo;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import org.springframework.stereotype.Component;
@Data
@TableName("dialog")
public class Dialog {

    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    @TableField("userid")
    private Long userid;

    @TableField("categoryid")
    private Long categoryid;

    @TableField("message")
    private String message;

    @TableField("sequence")
    private Long sequence;

    @TableField("dtype")
    private String dtype;

}