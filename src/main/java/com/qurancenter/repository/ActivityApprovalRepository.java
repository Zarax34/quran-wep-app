package com.qurancenter.repository;

import com.qurancenter.model.ActivityApproval;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ActivityApprovalRepository extends JpaRepository<ActivityApproval, Integer> {
    Optional<ActivityApproval> findByStudentIdAndActivityId(Integer studentId, Integer activityId);
}
