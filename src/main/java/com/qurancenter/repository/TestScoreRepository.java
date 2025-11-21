package com.qurancenter.repository;

import com.qurancenter.model.TestScore;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface TestScoreRepository extends JpaRepository<TestScore, Integer> {
    Optional<TestScore> findByTestIdAndStudentId(Integer testId, Integer studentId);
}
