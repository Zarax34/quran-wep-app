package com.qurancenter.repository;

import com.qurancenter.model.Settings;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SettingsRepository extends JpaRepository<Settings, Integer> {
    // Usually only one row
}
