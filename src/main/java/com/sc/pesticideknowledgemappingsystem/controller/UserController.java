package com.sc.pesticideknowledgemappingsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.sc.pesticideknowledgemappingsystem.dao.DialogDao;
import com.sc.pesticideknowledgemappingsystem.dao.UserDao;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@Controller
@CrossOrigin(origins = "*")
public class UserController {
    @Autowired
    private UserDao userDao;
    @Autowired
    private DialogDao dialogDao;

    @PostMapping("/register")
    @ResponseBody
    public String handleRegistration(@RequestBody Map<String, String> requestBody) {
        //从前端发来的请求中提取出信息
        String username = requestBody.get("username");
        String password = requestBody.get("password");
        String question = requestBody.get("question");
        String answer = requestBody.get("answer");


        // 检查用户名和密码是否为空
        if (username == null || password == null || username.isEmpty() || password.isEmpty()) {
            return "失败";
        }

        // 检查用户名是否已存在
        User existingUser = userDao.findByUsername(username);
        if (existingUser != null) {
            return "该用户已存在";
        }

        // 创建新用户对象
        User newUser = new User();
        newUser.setUsername(username);
        newUser.setPassword(password);
        newUser.setSecurityQuestion(question);
        newUser.setSecurityAnswer(answer);
        newUser.setRole("user");
        newUser.setIsDelete(0);

        // 将新用户保存到数据库
        userDao.insert(newUser);

        return username;
    }

    @PostMapping("/login")
    @ResponseBody
    public String Login(@RequestBody Map<String, String> requestBody) {
        String username = requestBody.get("username");
        String password = requestBody.get("password");
        // 根据用户名和密码查询用户
        User user = userDao.selectOne(new QueryWrapper<User>()
                .eq("username", username)
                .eq("password", password));

        if (user != null) {
            return username;
        } else {
            return "失败";
        }
    }

    @PostMapping("/question")
    @ResponseBody
    public String getQustion(@RequestBody Map<String, String> requestBody) {
        String username = requestBody.get("username");

        // 根据用户名和密码查询用户
        User user = userDao.selectOne(new QueryWrapper<User>()
                .eq("username", username));

        return user.getSecurityQuestion();
    }

    @PostMapping("/reset")
    @ResponseBody
    public String reset(@RequestBody Map<String, String> requestBody) {
        String username = requestBody.get("username");
        String answer = requestBody.get("answer");
        String password = requestBody.get("password");

        // 根据用户名和密码查询用户
        User user = userDao.selectOne(new QueryWrapper<User>()
                .eq("username", username)
                .eq("security_answer", answer));

        if (null == user) {
            return "失败";
        }

        user.setPassword(password);

        userDao.updateById(user);

        return "成功";
    }

    @PostMapping("/getusers")
    @ResponseBody
    public List<User> getAllUsers() {
        System.out.println(userDao.getAllUsers());
        return userDao.getAllUsers();
    }

    @PostMapping("/deleteUser")
    @ResponseBody
    public String deleteUser(@RequestBody Map<String, String> requestBody) {
        Long id = Long.valueOf(requestBody.get("id"));

        dialogDao.deleteDialogsByUserId(id);

        // 根据ID查询User
        User user = userDao.selectById(id);

        if (user != null) {
            // 将isDelete字段更改为1
            user.setIsDelete(1);
            userDao.updateById(user);
        }

        return "成功";
    }

    @PostMapping("/users/{username}")
    @ResponseBody
    public User findUser(@PathVariable("username") String username) {
        return userDao.findByUsername(username);
    }
}
