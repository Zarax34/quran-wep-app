package com.qurancenter.repository;

import com.qurancenter.model.StudentBadge;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface StudentBadgeRepository extends JpaRepository<StudentBadge, Integer> {
    List<StudentBadge> findByStudentId(Integer studentId);
}
