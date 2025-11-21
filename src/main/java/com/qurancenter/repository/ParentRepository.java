package com.qurancenter.repository;

import com.qurancenter.model.Parent;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ParentRepository extends JpaRepository<Parent, Integer> {
    Optional<Parent> findByPhone(String phone);
    Optional<Parent> findByUserId(Integer userId);
    Optional<Parent> findByName(String name);
}
