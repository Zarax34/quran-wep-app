package com.qurancenter.repository;

import com.qurancenter.model.Work;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface WorkRepository extends JpaRepository<Work, Integer> {
    List<Work> findAllByOrderByCreatedAtDesc();
}
