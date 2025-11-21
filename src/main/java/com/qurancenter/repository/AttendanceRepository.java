package com.qurancenter.repository;

import com.qurancenter.model.Attendance;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface AttendanceRepository extends JpaRepository<Attendance, Integer> {
    List<Attendance> findByStudentIdAndDateBetween(Integer studentId, LocalDate startDate, LocalDate endDate);
    Optional<Attendance> findByStudentIdAndDate(Integer studentId, LocalDate date);
    List<Attendance> findByDate(LocalDate date);
}
