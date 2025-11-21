package com.qurancenter.repository;

import com.qurancenter.model.Alumni;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AlumniRepository extends JpaRepository<Alumni, Integer> {
    List<Alumni> findAllByOrderByGraduationYearDesc();
}
