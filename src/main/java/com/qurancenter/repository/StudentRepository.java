package com.qurancenter.repository;

import com.qurancenter.model.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface StudentRepository extends JpaRepository<Student, Integer> {
    List<Student> findByCircleIdAndIsActiveTrue(Integer circleId);
    List<Student> findByIsActiveTrue();
    List<Student> findByParentIdAndIsActiveTrue(Integer parentId);
}
