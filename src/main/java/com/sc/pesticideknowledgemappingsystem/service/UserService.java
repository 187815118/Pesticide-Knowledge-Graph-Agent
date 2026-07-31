package com.sc.pesticideknowledgemappingsystem.service;

import com.github.javafaker.Faker;
import com.sc.pesticideknowledgemappingsystem.dao.UserDao;
import com.sc.pesticideknowledgemappingsystem.entity.pojo.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class UserService {
    @Autowired
    private UserDao userDao;

    Faker faker = new Faker();

    public void createRandomUser() {
        for (int i = 0; i < 300; i++) {
            User user = new User();
            user.setUsername(faker.name().username());
            user.setPassword(faker.internet().password());
            user.setSecurityQuestion(faker.lorem().sentence());
            user.setSecurityAnswer(faker.lorem().word());
            user.setRole("user");
            user.setIsDelete(0);

            userDao.insert(user);
        }
    }
}