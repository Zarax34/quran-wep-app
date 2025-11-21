package com.qurancenter.repository;

import com.qurancenter.model.HonorBoard;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface HonorBoardRepository extends JpaRepository<HonorBoard, Integer> {
    List<HonorBoard> findByMonthAndYearOrderByRankAsc(Integer month, Integer year);
    void deleteByMonthAndYear(Integer month, Integer year);
}
