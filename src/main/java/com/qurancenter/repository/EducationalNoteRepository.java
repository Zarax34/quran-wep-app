package com.qurancenter.repository;

import com.qurancenter.model.EducationalNote;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface EducationalNoteRepository extends JpaRepository<EducationalNote, Integer> {
    List<EducationalNote> findByStudentIdOrderByDateDesc(Integer studentId);
}
