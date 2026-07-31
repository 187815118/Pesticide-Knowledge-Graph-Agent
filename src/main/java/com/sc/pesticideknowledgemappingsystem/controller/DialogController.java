package com.sc.pesticideknowledgemappingsystem.controller;

import com.sc.pesticideknowledgemappingsystem.dao.DialogDao;
import com.sc.pesticideknowledgemappingsystem.dao.UserDao;
import com.sc.pesticideknowledgemappingsystem.entity.dto.DialogDto;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.Dialog;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.User;
import com.sc.pesticideknowledgemappingsystem.service.DialogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Controller
@CrossOrigin(origins = "*")
public class DialogController {
    @Autowired
    private DialogService dialogService;

    @Autowired
    private UserDao userDao;

    @PostMapping("/dialogs")
    @ResponseBody //请求参数以json返回
    public Map<String, String> getDialogsByUsername(@RequestBody Map<String, String> requestBody) {
        // 从请求体中获取用户名
        String username = requestBody.get("username");
        String categoryId = requestBody.get("categoryId");

        if (categoryId != null) {
            Map<String, String> dialogsByUserNameAndCategoryId = dialogService.getDialogsByUserNameAndCategoryId(username, categoryId);
            return dialogService.getDialogsByUserNameAndCategoryId(username, categoryId);
        }

        //如果没有指定，默认category为1
        System.out.println(dialogService.getDialogsByUserNameAndCategoryId(username, "1"));
        return dialogService.getDialogsByUserNameAndCategoryId(username, "1");
    }

    /*获取对话列表*/
    @PostMapping("/dialogsall")
    @ResponseBody
    public Map<Long, String> getAllDialogsByUsername(@RequestBody Map<String, String> requestBody) {
        String username = requestBody.get("username");
        return dialogService.getAllDialogsByUsername(username);
    }


    @PostMapping("/dialogsdelete")
    @ResponseBody
    public String deleteDialogsByUserNameAndCategoryId(@RequestBody Map<String, String> requestBody) {
        // 从请求体中获取用户名
        String username = requestBody.get("username");
        String categoryId = requestBody.get("categoryId");

        dialogService.deleteDialogsByUserNameAndCategoryId(username, Long.valueOf(categoryId));

        return "删除成功";
    }

    @Autowired
    private DialogDao dialogDao;

    @PostMapping("/getDialogs")
    @ResponseBody
    public List<DialogDto> getDialogs() {
        List<Dialog> dialogList = dialogDao.getAllDialogs();
        List<DialogDto> dialogDtoList = new ArrayList<>();

        for (Dialog dialog : dialogList) {
            DialogDto dialogDto = new DialogDto();
            dialogDto.setId(dialog.getId());
            dialogDto.setUsername(getUsernameById(dialog.getUserid()));
            dialogDto.setCategoryid(dialog.getCategoryid());
            dialogDto.setMessage(dialog.getMessage());
            dialogDto.setSequence(dialog.getSequence());
            dialogDto.setDtype(dialog.getDtype());

            dialogDtoList.add(dialogDto);
        }

        return dialogDtoList;
    }

    private String getUsernameById(Long userId) {
        User user = userDao.selectById(userId);
        if (user != null) {
            return user.getUsername();
        }
        return null;
    }

}
