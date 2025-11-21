package com.qurancenter.repository;

import com.qurancenter.model.MonthlyPlan;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface MonthlyPlanRepository extends JpaRepository<MonthlyPlan, Integer> {
    Optional<MonthlyPlan> findFirstByStudentIdOrderByCreatedAtDesc(Integer studentId);
}
