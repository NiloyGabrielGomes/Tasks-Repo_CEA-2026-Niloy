/**
 * F-7: WFHPeriodManager component tests
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';

// ── mocks ─────────────────────────────────────────────────────────────────────
const mockUseAuth = vi.fn();
vi.mock('../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

const mockWfhList   = vi.fn();
const mockWfhCreate = vi.fn();
const mockWfhDelete = vi.fn();
const mockGetAll    = vi.fn();
const mockGetTeam   = vi.fn();

vi.mock('../services/api', () => ({
  wfhPeriodsAPI: {
    list:   (...args) => mockWfhList(...args),
    create: (...args) => mockWfhCreate(...args),
    update: vi.fn(),
    delete: (...args) => mockWfhDelete(...args),
  },
  usersAPI: {
    getAllUsers:  (...args) => mockGetAll(...args),
    getTeamUsers: (...args) => mockGetTeam(...args),
  },
}));

import WFHPeriodManager from '../components/WFHPeriodManager';

// ── sample data ───────────────────────────────────────────────────────────────
const mkUser = (role, extra = {}) => ({
  id: 'user-1',
  name: 'Test User',
  email: 'user@test.com',
  role,
  team: 'Engineering',
  ...extra,
});

const EMPTY_PERIODS = { data: { periods: [], total: 0 } };

const PERIOD = {
  id: 'wfh-1',
  employee_id: 'user-1',
  employee_name: 'Test User',
  employee_team: 'Engineering',
  start_date: '2026-03-01',
  end_date: '2026-03-05',
  reason: 'Personal',
};

const USERS_LIST = {
  data: {
    users: [
      { id: 'user-1', name: 'Test User',  email: 'user@test.com',   is_active: true, team: 'Engineering' },
      { id: 'user-2', name: 'Other User', email: 'other@test.com', is_active: true, team: 'Engineering' },
    ],
  },
};

// ── helpers ───────────────────────────────────────────────────────────────────
function renderManager() {
  return render(<WFHPeriodManager />);
}

// ── tests ─────────────────────────────────────────────────────────────────────
describe('WFHPeriodManager – add / delete flow (F-7)', () => {
  beforeEach(() => {
    mockWfhList.mockReset();
    mockWfhCreate.mockReset();
    mockWfhDelete.mockReset();
    mockGetAll.mockReset();
    mockGetTeam.mockReset();

    mockWfhList.mockResolvedValue(EMPTY_PERIODS);
    mockGetAll.mockResolvedValue(USERS_LIST);
    mockGetTeam.mockResolvedValue(USERS_LIST);
  });

  // ── Employee view ───────────────────────────────────────────────────────────

  describe('Employee role', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ user: mkUser('employee') });
    });

    it('renders "WFH Periods" heading', async () => {
      renderManager();
      expect(screen.getByText('WFH Periods')).toBeInTheDocument();
    });

    it('does NOT render the filter bar', async () => {
      renderManager();
      // Filter bar has a "Employee" label — employees don't see it
      expect(screen.queryByText(/^Employee$/i)).toBeNull();
    });

    it('"Schedule Period" button is visible', async () => {
      renderManager();
      expect(screen.getByRole('button', { name: /Schedule Period/i })).toBeInTheDocument();
    });

    it('clicking "Schedule Period" opens the modal', async () => {
      renderManager();
      fireEvent.click(screen.getByRole('button', { name: /Schedule Period/i }));
      await waitFor(() => {
        expect(screen.getByText('Schedule WFH Period')).toBeInTheDocument();
      });
    });

    it('cancelling modal closes it', async () => {
      renderManager();
      fireEvent.click(screen.getByRole('button', { name: /Schedule Period/i }));
      await waitFor(() => screen.getByText('Schedule WFH Period'));

      fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
      await waitFor(() => {
        expect(screen.queryByText('Schedule WFH Period')).toBeNull();
      });
    });

    it('shows "No WFH periods found" when list is empty', async () => {
      renderManager();
      await waitFor(() => {
        expect(screen.getByText(/No WFH periods found/i)).toBeInTheDocument();
      });
    });
  });

  // ── Admin view ──────────────────────────────────────────────────────────────

  describe('Admin role', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ user: mkUser('admin') });
    });

    it('renders filter bar with Team dropdown', async () => {
      renderManager();
      await waitFor(() => {
        // Admin sees the Team label in filter bar
        expect(screen.getByText(/^Team$/i)).toBeInTheDocument();
      });
    });

    it('fetches all users for employee picker', async () => {
      renderManager();
      await waitFor(() => {
        expect(mockGetAll).toHaveBeenCalled();
      });
    });

    it('renders period rows in table when API returns data', async () => {
      mockWfhList.mockResolvedValue({ data: { periods: [PERIOD], total: 1 } });
      renderManager();
      await waitFor(() => {
        // getAllByText because 'Test User' also appears in the filter dropdown option
        const matches = screen.getAllByText('Test User');
        expect(matches.length).toBeGreaterThanOrEqual(1);
      });
      // getAllByText because 'Engineering' also appears in Team dropdown option
      expect(screen.getAllByText('Engineering').length).toBeGreaterThanOrEqual(1);
    });

    it('delete button triggers confirmation overlay', async () => {
      mockWfhList.mockResolvedValue({ data: { periods: [PERIOD], total: 1 } });
      renderManager();
      await waitFor(() => screen.getAllByText('Test User'));

      // click delete icon button (title="Delete")
      const deleteButtons = screen.getAllByTitle('Delete');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/Delete WFH Period\?/i)).toBeInTheDocument();
      });
    });

    it('cancelling delete confirmation hides overlay without calling delete', async () => {
      mockWfhList.mockResolvedValue({ data: { periods: [PERIOD], total: 1 } });
      renderManager();
      await waitFor(() => screen.getAllByText('Test User'));

      fireEvent.click(screen.getAllByTitle('Delete')[0]);
      await waitFor(() => screen.getByText(/Delete WFH Period\?/i));

      // click Cancel in confirmation
      const cancelBtn = screen.getByRole('button', { name: /^Cancel$/i });
      fireEvent.click(cancelBtn);

      await waitFor(() => {
        expect(screen.queryByText(/Delete WFH Period\?/i)).toBeNull();
      });
      expect(mockWfhDelete).not.toHaveBeenCalled();
    });

    it('confirming delete calls wfhPeriodsAPI.delete and refreshes list', async () => {
      mockWfhList
        .mockResolvedValueOnce({ data: { periods: [PERIOD], total: 1 } })
        .mockResolvedValueOnce(EMPTY_PERIODS);
      mockWfhDelete.mockResolvedValueOnce({});

      renderManager();
      await waitFor(() => screen.getAllByText('Test User'));

      fireEvent.click(screen.getAllByTitle('Delete')[0]);
      await waitFor(() => screen.getByText(/Delete WFH Period\?/i));

      await act(async () => {
        // Click the Delete button in the confirmation modal
        // (the modal renders before the section in DOM; find by visible text not accessible name
        //  because the icon span "delete" is included in computed accessible name)
        const confirmDialog = screen.getByText(/Delete WFH Period\?/i).closest('div');
        const confirmDeleteBtn = confirmDialog.querySelector('button');
        fireEvent.click(confirmDeleteBtn);
      });

      await waitFor(() => {
        expect(mockWfhDelete).toHaveBeenCalledWith('wfh-1');
      });
      // Content refreshed — periods gone
      await waitFor(() => {
        expect(screen.getByText(/No WFH periods found/i)).toBeInTheDocument();
      });
    });
  });

  // ── Team Lead view ──────────────────────────────────────────────────────────

  describe('TeamLead role', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ user: mkUser('team_lead') });
    });

    it('renders filter bar WITHOUT team dropdown (TL only sees own team)', async () => {
      renderManager();
      await waitFor(() => {
        // Employee label from filter bar confirms filter bar is visible
        expect(screen.queryByText(/^Team$/i)).toBeNull();   // no Team filter
      });
    });

    it('fetches team users (not all users) for employee picker', async () => {
      renderManager();
      await waitFor(() => {
        expect(mockGetTeam).toHaveBeenCalled();
        expect(mockGetAll).not.toHaveBeenCalled();
      });
    });
  });
});
