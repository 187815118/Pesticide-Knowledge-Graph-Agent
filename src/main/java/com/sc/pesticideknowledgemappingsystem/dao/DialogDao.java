package com.sc.pesticideknowledgemappingsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.Dialog;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.springframework.data.repository.query.Param;

import java.util.List;



@Mapper
public interface DialogDao extends BaseMapper<Dialog> {
    @Select("SELECT * FROM dialog")
    List<Dialog> getAllDialogs();

    // 根据 categoryId 和 userId 获取对话列表
    @Select("SELECT * FROM dialog WHERE userid = #{userId} AND categoryid = #{categoryId}")
    List<Dialog> findByUserIdAndCategoryId(@Param("userId") Long userId, @Param("categoryId") Long categoryId);

    @Select("SELECT * FROM dialog WHERE userid = #{userId}")
    List<Dialog> findByUserId(@Param("userId") Long userId);

    @Delete("DELETE FROM dialog WHERE userid = #{userId}")
    void deleteDialogsByUserId(@Param("userId") Long userId);


}