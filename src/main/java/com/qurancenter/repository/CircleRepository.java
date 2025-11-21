package com.qurancenter.repository;

import com.qurancenter.model.Circle;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CircleRepository extends JpaRepository<Circle, Integer> {
    List<Circle> findByTeacherId(Integer teacherId);
    List<Circle> findByIsActiveTrue();
}
