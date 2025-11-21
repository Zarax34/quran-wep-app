package com.qurancenter.repository;

import com.qurancenter.model.Holiday;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDate;
import java.util.List;

public interface HolidayRepository extends JpaRepository<Holiday, Integer> {
    List<Holiday> findByDateBetween(LocalDate startDate, LocalDate endDate);
    boolean existsByDate(LocalDate date);
}
