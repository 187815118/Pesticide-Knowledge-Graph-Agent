package com.sc.pesticideknowledgemappingsystem.controller;

import com.sc.pesticideknowledgemappingsystem.service.NewAnswerService;
import com.sc.pesticideknowledgemappingsystem.service.DialogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.Map;

@Controller
@CrossOrigin(origins = "*") //它的作用是允许跨域请求，即允许来自不同源的HTTP请求访问当前的接口。
public class AnswerController {

    @Autowired
    private NewAnswerService answerService;
    @Autowired
    private DialogService dialogService;

    @PostMapping("/answer")
    @ResponseBody
    public String handleQuestion(@RequestBody Map<String, String> requestBody) throws IOException {
        //从请求中获取参数
        String question = requestBody.get("question");
        String username = requestBody.get("username");
        String categoryId = requestBody.get("categoryId");

        //上面接受请求后得出请求里面的参数，现在调用Service进行逻辑处理
        String answer = answerService.Bayes(question);
        if(answer.equals("Xiaozhi is still young and doesn't know what you're talking about~")){

        }

        if (username != null) {
            dialogService.saveDialogs(username, categoryId, question, answer);
        }
        System.out.println(answer);
        System.out.println("Controller");
        return answer;
    }



}