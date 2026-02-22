/**
 * F-7: AnnouncementDraft component tests
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

// ── mock announcementsAPI ─────────────────────────────────────────────────────
const mockCreateDraft = vi.fn();
const mockPublish     = vi.fn();
const mockList        = vi.fn();

vi.mock('../services/api', () => ({
  announcementsAPI: {
    createDraft: (...args) => mockCreateDraft(...args),
    publish:     (...args) => mockPublish(...args),
    list:        (...args) => mockList(...args),
  },
}));

import AnnouncementDraft from '../components/AnnouncementDraft';

// ── helpers ──────────────────────────────────────────────────────────────────
const EMPTY_LIST = { data: { announcements: [] } };

const DRAFT_ITEM = {
  id: 'ann-1',
  title: 'Test Announcement',
  body: 'Hello everyone!',
  status: 'draft',
  audience: 'all',
  created_at: new Date().toISOString(),
  scheduled_at: null,
  published_at: null,
};

function renderDraft() {
  return render(<AnnouncementDraft />);
}

// ── tests ─────────────────────────────────────────────────────────────────────
describe('AnnouncementDraft – form + draft save flow (F-7)', () => {
  beforeEach(() => {
    mockCreateDraft.mockReset();
    mockPublish.mockReset();
    mockList.mockReset();
    // Default: return empty list
    mockList.mockResolvedValue(EMPTY_LIST);
  });

  it('renders section heading "Announcements"', async () => {
    renderDraft();
    expect(screen.getByText('Announcements')).toBeInTheDocument();
  });

  it('form is collapsed by default — title input not visible', async () => {
    renderDraft();
    expect(screen.queryByPlaceholderText(/Enter announcement title/i)).toBeNull();
  });

  it('clicking "New Announcement" expands the form', async () => {
    renderDraft();
    fireEvent.click(screen.getByText('New Announcement'));
    expect(screen.getByPlaceholderText(/Enter announcement title/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Write your announcement/i)).toBeInTheDocument();
  });

  it('shows validation error when saving without title and body', async () => {
    renderDraft();
    // open form
    fireEvent.click(screen.getByText('New Announcement'));
    // click Save as Draft with empty fields
    fireEvent.click(screen.getByRole('button', { name: /Save as Draft/i }));
    expect(await screen.findByText(/Title and body are required/i)).toBeInTheDocument();
    expect(mockCreateDraft).not.toHaveBeenCalled();
  });

  it('shows error when only title is filled', async () => {
    renderDraft();
    fireEvent.click(screen.getByText('New Announcement'));
    const titleInput = screen.getByPlaceholderText(/Enter announcement title/i);
    await userEvent.type(titleInput, 'My Title');
    fireEvent.click(screen.getByRole('button', { name: /Save as Draft/i }));
    expect(await screen.findByText(/Title and body are required/i)).toBeInTheDocument();
    expect(mockCreateDraft).not.toHaveBeenCalled();
  });

  it('calls createDraft with correct args and collapses form on success', async () => {
    mockCreateDraft.mockResolvedValueOnce({ data: { id: 'ann-new' } });
    // list re-fetches after creation — return same empty list
    mockList.mockResolvedValue(EMPTY_LIST);

    renderDraft();
    fireEvent.click(screen.getByText('New Announcement'));

    const titleInput = screen.getByPlaceholderText(/Enter announcement title/i);
    const bodyInput  = screen.getByPlaceholderText(/Write your announcement/i);

    await userEvent.type(titleInput, 'Hello World');
    await userEvent.type(bodyInput,  'This is the body.');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Save as Draft/i }));
    });

    await waitFor(() => {
      expect(mockCreateDraft).toHaveBeenCalledWith('Hello World', 'This is the body.', 'all', null);
    });

    // form should collapse (title input no longer visible)
    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/Enter announcement title/i)).toBeNull();
    });
  });

  it('shows API error message when createDraft rejects', async () => {
    mockCreateDraft.mockRejectedValueOnce({
      response: { data: { detail: 'Permission denied.' } },
    });

    renderDraft();
    fireEvent.click(screen.getByText('New Announcement'));

    const titleInput = screen.getByPlaceholderText(/Enter announcement title/i);
    const bodyInput  = screen.getByPlaceholderText(/Write your announcement/i);

    await userEvent.type(titleInput, 'Fail Test');
    await userEvent.type(bodyInput, 'Body content here.');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Save as Draft/i }));
    });

    expect(await screen.findByText('Permission denied.')).toBeInTheDocument();
  });

  it('DraftList shows "No announcements found" when list is empty', async () => {
    mockList.mockResolvedValue(EMPTY_LIST);
    renderDraft();
    await waitFor(() => {
      expect(screen.getByText(/No announcements found/i)).toBeInTheDocument();
    });
  });

  it('DraftList renders announcement items from API', async () => {
    mockList.mockResolvedValue({ data: { announcements: [DRAFT_ITEM] } });
    renderDraft();
    await waitFor(() => {
      expect(screen.getByText('Test Announcement')).toBeInTheDocument();
    });
    // Status badge
    expect(screen.getByText('draft')).toBeInTheDocument();
    // Publish button
    expect(screen.getByRole('button', { name: /Publish Now/i })).toBeInTheDocument();
  });

  it('"Publish Now" calls announcementsAPI.publish with item id', async () => {
    mockList.mockResolvedValueOnce({ data: { announcements: [DRAFT_ITEM] } });
    mockPublish.mockResolvedValueOnce({ data: { ...DRAFT_ITEM, status: 'sent' } });
    // After publish, list re-fetches and returns empty
    mockList.mockResolvedValue(EMPTY_LIST);

    renderDraft();
    await waitFor(() => screen.getByRole('button', { name: /Publish Now/i }));

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Publish Now/i }));
    });

    await waitFor(() => {
      expect(mockPublish).toHaveBeenCalledWith('ann-1', null);
    });
  });

  it('status filter tabs are rendered (All, Drafts, Scheduled, Sent)', async () => {
    renderDraft();
    expect(screen.getByRole('button', { name: /^All$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Drafts$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Scheduled$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Sent$/i })).toBeInTheDocument();
  });

  it('clicking "Drafts" filter re-fetches with status="draft"', async () => {
    mockList.mockResolvedValue(EMPTY_LIST);
    renderDraft();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Drafts$/i }));
    });

    await waitFor(() => {
      // Should have been called at least once with 'draft' argument
      expect(mockList).toHaveBeenCalledWith('draft');
    });
  });
});
