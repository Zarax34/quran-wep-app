package com.qurancenter.repository;

import com.qurancenter.model.Report;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDate;
import java.util.List;

public interface ReportRepository extends JpaRepository<Report, Integer> {
    List<Report> findByStudentId(Integer studentId);
    List<Report> findByStudentIdAndDateBetween(Integer studentId, LocalDate startDate, LocalDate endDate);
    List<Report> findByDate(LocalDate date);
    long countByStudentId(Integer studentId);
}
