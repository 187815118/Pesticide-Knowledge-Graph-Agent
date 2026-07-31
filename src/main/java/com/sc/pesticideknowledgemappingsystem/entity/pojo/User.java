package com.sc.pesticideknowledgemappingsystem.entity.pojo;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
@TableName("user")
@Data
public class User {

    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    @TableField("username")
    private String username;

    @TableField("password")
    private String password;

    @TableField("security_question")
    private String securityQuestion;

    @TableField("security_answer")
    private String securityAnswer;

    @TableField("role")
    private String role;

    @TableField("is_delete")
    private Integer isDelete;

    @TableField("create_time")
    private Date createTime;

}