package com.sc.pesticideknowledgemappingsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.sc.pesticideknowledgemappingsystem.dao.DialogDao;
import com.sc.pesticideknowledgemappingsystem.dao.UserDao;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.Dialog;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.User;
import org.apache.coyote.http11.filters.IdentityOutputFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class DialogService {

    @Autowired
    private UserDao userDao;

    @Autowired
    private DialogDao dialogDao;

    public Map<String, String> getUsernameAndDialogs(String username) {
        // 通过用户名从数据库中获取用户信息
        User user = userDao.findByUsername(username);

        // 通过userID从数据库中获取对话列表
        List<Dialog> dialogList = dialogDao.findByUserId(user.getId());

        // 过滤出categoryid等于1的对话
        List<Dialog> dialogs = dialogList.stream()
                .filter(dialog -> dialog.getCategoryid() == 1)
                .collect(Collectors.toList());

        // 创建一个有序的Map来存储键值对
        Map<String, String> orderedMap = new LinkedHashMap<>();

        // 遍历过滤后的对话列表，并按照sequence顺序添加到有序Map中
        for (int i = 0; i < dialogs.size(); i += 2) {
            Dialog questionDialog = dialogs.get(i);
            Dialog answerDialog = dialogs.get(i + 1);

            // 组合消息对，并按照sequence存储到有序Map中
            String questionMessage = questionDialog.getMessage();
            String answerMessage = answerDialog.getMessage();
            orderedMap.put(questionMessage, answerMessage);
        }

        return orderedMap;
    }

    public boolean containsCategoryId(List<Dialog> dialogList, String categoryId) {
        for (Dialog dialog : dialogList) {
            if (String.valueOf(dialog.getCategoryid()).equals(categoryId)) {
                return true;
            }
        }
        return false;
    }


    public void saveDialogs(String userName, String categoryId, String question, String answer) {
        // 通过用户名从数据库中获取用户信息
        User user = userDao.findByUsername(userName);
        System.out.println(user);

        // 通过userID从数据库中获取对话列表
        List<Dialog> dialogList = dialogDao.findByUserId(user.getId());

        boolean containsCategoryId = containsCategoryId(dialogList, categoryId);

        if (containsCategoryId) {
            // 包含 categoryId 的逻辑处理

            // 找到 dialogList 中 sequence 的最大值
            OptionalInt maxSequenceOptional = dialogList.stream()
                    .mapToInt(dialog -> dialog.getSequence().intValue()) // 将Long类型转换为int类型
                    .max(); // 找到整数流中的最大值

            // 将最大值加一赋值给 sequence，如果找不到最大值，则将 1 赋值给 sequence
            long sequence = maxSequenceOptional.orElse(0) + 1;

            Dialog dialog = new Dialog();
            dialog.setUserid(user.getId());
            dialog.setCategoryid(Long.valueOf(categoryId));
            dialog.setMessage(question);
            dialog.setSequence(sequence);
            dialog.setDtype("q");

            dialogDao.insert(dialog);

            dialog.setMessage(answer);
            dialog.setDtype("a");

            dialogDao.insert(dialog);

        } else {
            // 不包含 categoryId 的逻辑处理
            Dialog dialog = new Dialog();
            dialog.setUserid(user.getId());
            dialog.setCategoryid(Long.valueOf(categoryId));
            dialog.setMessage(question);
            dialog.setSequence(1L);
            dialog.setDtype("q");

            dialogDao.insert(dialog);

            dialog.setMessage(answer);
            dialog.setDtype("a");

            dialogDao.insert(dialog);
        }


    }

    public Map<String, String> getDialogsByUserNameAndCategoryId(String username, String categoryId) {
        // 通过用户名从数据库中获取用户信息
        User user = userDao.findByUsername(username);

        // 通过userID从数据库中获取对话列表
        List<Dialog> dialogList = dialogDao.findByUserId(user.getId());

        // 过滤出categoryid等于categoryId的对话
        List<Dialog> dialogs = dialogList.stream()
                .filter(dialog -> dialog.getCategoryid() == Integer.parseInt(categoryId))
                .collect(Collectors.toList());


        // 创建一个有序的Map来存储键值对
        Map<String, String> orderedMap = new LinkedHashMap<>();

//         遍历过滤后的对话列表，并按照sequence顺序添加到有序Map中
        for (int i = 0; i < dialogs.size(); i += 2) {
            Dialog questionDialog = dialogs.get(i);
            Dialog answerDialog = dialogs.get(i + 1);

            // 组合消息对，并按照sequence存储到有序Map中
            String questionMessage = questionDialog.getMessage();
            String answerMessage = answerDialog.getMessage();
            orderedMap.put(questionMessage, answerMessage);
        }

        return orderedMap;
    }

    public Map<Long, String> getAllDialogsByUsername(String userName) {
        // 通过用户名从数据库中获取用户信息
        User user = userDao.findByUsername(userName);

        // 通过userID从数据库中获取对话列表
        List<Dialog> dialogList = dialogDao.findByUserId(user.getId());

        // 创建有序的 Map 来存储结果
        Map<Long, String> categoryMessages = new LinkedHashMap<>();
        for (Dialog dialog : dialogList) {
            if (dialog.getSequence() == 1 && "q".equals(dialog.getDtype())) {
                String message = dialog.getMessage();
                /*问题超过10字符则截取加省略号*/
                if (message.length() > 26) {
                    message = message.substring(0, 25) + "...";
                }
                categoryMessages.put(dialog.getCategoryid(), message);
            }
        }

        return categoryMessages;

    }

    // 根据用户id和categoryid删除对话
    public void deleteDialogsByUserNameAndCategoryId(String userName, Long categoryId) {
        // 通过用户名从数据库中获取用户信息
        User user = userDao.findByUsername(userName);

        dialogDao.delete(new QueryWrapper<Dialog>()
                .eq("userid", user.getId())
                .eq("categoryid", categoryId));
    }

}
