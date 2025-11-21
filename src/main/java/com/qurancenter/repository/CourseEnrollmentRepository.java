package com.qurancenter.repository;

import com.qurancenter.model.CourseEnrollment;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface CourseEnrollmentRepository extends JpaRepository<CourseEnrollment, Integer> {
    Optional<CourseEnrollment> findByCourseIdAndStudentId(Integer courseId, Integer studentId);
}
