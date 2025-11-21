package com.qurancenter.repository;

import com.qurancenter.model.Course;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CourseRepository extends JpaRepository<Course, Integer> {
    List<Course> findByIsActiveTrue();
}
