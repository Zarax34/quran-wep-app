package com.qurancenter.repository;

import com.qurancenter.model.ParentNote;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ParentNoteRepository extends JpaRepository<ParentNote, Integer> {
    List<ParentNote> findAllByOrderByCreatedAtDesc();
}
