package com.sc.pesticideknowledgemappingsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.springframework.data.repository.query.Param;

import java.util.List;

@Mapper
public interface UserDao extends BaseMapper<User> {
    @Select("SELECT * FROM user")
    List<User> getAllUsers();

    @Select("SELECT * FROM user WHERE username = #{username}")
    User findByUsername(@Param("username") String username);
}