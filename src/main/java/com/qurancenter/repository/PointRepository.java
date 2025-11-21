package com.qurancenter.repository;

import com.qurancenter.model.Point;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface PointRepository extends JpaRepository<Point, Integer> {
    @Query("SELECT SUM(p.points) FROM Point p WHERE p.studentId = :studentId")
    Integer sumPointsByStudentId(Integer studentId);
}
