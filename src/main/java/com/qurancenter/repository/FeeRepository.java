package com.qurancenter.repository;

import com.qurancenter.model.Fee;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface FeeRepository extends JpaRepository<Fee, Integer> {
    List<Fee> findByStudentId(Integer studentId);
}
