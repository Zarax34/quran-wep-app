package com.qurancenter.repository;

import com.qurancenter.model.UserLogin;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface UserLoginRepository extends JpaRepository<UserLogin, Integer> {
    List<UserLogin> findAllByOrderByLoginTimeDesc();
}
