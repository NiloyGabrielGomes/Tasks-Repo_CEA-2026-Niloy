/**
 * F-7: HeadcountTable view-toggle tests
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';

// ── mock headcountAPI ────────────────────────────────────────────────────────
const mockByTeam    = vi.fn();
const mockByLocation = vi.fn();
vi.mock('../services/api', () => ({
  headcountAPI: {
    byTeam:     (...args) => mockByTeam(...args),
    byLocation: (...args) => mockByLocation(...args),
  },
}));

import HeadcountTable from '../components/HeadcountTable';

// ── sample data ──────────────────────────────────────────────────────────────
const TEAM_RESPONSE = {
  data: {
    total_employees: 3,
    teams: [
      {
        team: 'Engineering',
        total_members: 3,
        office_count: 2,
        wfh_count: 1,
        members: [
          { user_id: '1', name: 'Alice', email: 'a@test.com', location: 'Office' },
          { user_id: '2', name: 'Bob',   email: 'b@test.com', location: 'WFH'    },
          { user_id: '3', name: 'Carol', email: 'c@test.com', location: 'Office' },
        ],
      },
    ],
  },
};

const LOCATION_RESPONSE = {
  data: {
    total_employees: 3,
    locations: [
      {
        location: 'Office',
        count: 2,
        employees: [
          { user_id: '1', name: 'Alice', email: 'a@test.com', team: 'Engineering' },
          { user_id: '3', name: 'Carol', email: 'c@test.com', team: 'Engineering' },
        ],
      },
      {
        location: 'WFH',
        count: 1,
        employees: [
          { user_id: '2', name: 'Bob', email: 'b@test.com', team: 'Engineering' },
        ],
      },
    ],
  },
};

const DEFAULT_HEADCOUNT = { lunch: 5, snacks: 3 };
const TEST_DATE = '2026-02-22';

// ── helpers ──────────────────────────────────────────────────────────────────
function renderTable(props = {}) {
  return render(
    <HeadcountTable
      headcount={DEFAULT_HEADCOUNT}
      totalUsers={10}
      date={TEST_DATE}
      refreshKey={0}
      {...props}
    />,
  );
}

// ── tests ────────────────────────────────────────────────────────────────────
describe('HeadcountTable – view toggles (F-6 / F-7)', () => {
  beforeEach(() => {
    mockByTeam.mockReset();
    mockByLocation.mockReset();
  });

  it('renders heading and three tab buttons', () => {
    renderTable();
    expect(screen.getByText('Headcount Summary')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Meals/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /By Team/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /By Location/i })).toBeInTheDocument();
  });

  it('default active tab is Meals and shows meal bars', () => {
    renderTable();
    // MealsPanel renders meal names from MEAL_LABELS
    expect(screen.getByText('Lunch')).toBeInTheDocument();
    expect(screen.getByText('Snacks')).toBeInTheDocument();
  });

  it('shows "No meal data available" when headcount is null', () => {
    renderTable({ headcount: null });
    expect(screen.getByText(/No meal data available/i)).toBeInTheDocument();
  });

  it('clicking "By Team" fetches team data and renders team summary', async () => {
    mockByTeam.mockResolvedValueOnce(TEAM_RESPONSE);

    renderTable();
    const teamTab = screen.getByRole('button', { name: /By Team/i });

    await act(async () => {
      fireEvent.click(teamTab);
    });

    expect(mockByTeam).toHaveBeenCalledWith(TEST_DATE);
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });
    // Summary strip shows active employee count (text is split across <strong> and text node)
    expect(screen.getByText((_, el) => el?.tagName === 'SPAN' && /3.*active employees/i.test(el.textContent))).toBeInTheDocument();
  });

  it('clicking "By Location" fetches location data and renders location bars', async () => {
    mockByLocation.mockResolvedValueOnce(LOCATION_RESPONSE);

    renderTable();
    const locTab = screen.getByRole('button', { name: /By Location/i });

    await act(async () => {
      fireEvent.click(locTab);
    });

    expect(mockByLocation).toHaveBeenCalledWith(TEST_DATE);
    await waitFor(() => {
      // Location labels appear in the UI
      expect(screen.getAllByText('Office').length).toBeGreaterThan(0);
      expect(screen.getAllByText('WFH').length).toBeGreaterThan(0);
    });
  });

  it('shows "Failed to load team breakdown" when byTeam rejects', async () => {
    mockByTeam.mockRejectedValueOnce(new Error('network error'));

    renderTable();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /By Team/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to load team breakdown/i)).toBeInTheDocument();
    });
  });

  it('shows "Failed to load location breakdown" when byLocation rejects', async () => {
    mockByLocation.mockRejectedValueOnce(new Error('network error'));

    renderTable();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /By Location/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Failed to load location breakdown/i)).toBeInTheDocument();
    });
  });

  it('switching back to Meals tab re-renders Meals panel', async () => {
    mockByTeam.mockResolvedValueOnce(TEAM_RESPONSE);

    renderTable();
    // go to By Team
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /By Team/i }));
    });
    await waitFor(() => screen.getByText('Engineering'));

    // back to Meals
    fireEvent.click(screen.getByRole('button', { name: /Meals/i }));
    expect(screen.getByText('Lunch')).toBeInTheDocument();
  });
});
