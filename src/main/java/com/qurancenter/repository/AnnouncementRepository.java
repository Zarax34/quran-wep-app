package com.qurancenter.repository;

import com.qurancenter.model.Announcement;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AnnouncementRepository extends JpaRepository<Announcement, Integer> {
    List<Announcement> findByIsActiveTrueOrderByDatePostedDesc();
}
